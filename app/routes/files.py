from app import app, db, admin_only, auto, ENTITY_MAPPING
from app.models import cfg_settings, files
from app.utilities import sha1
from flask import abort, jsonify, request, send_file, json, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import errno
import tempfile
import uuid
import shutil
import delegator
import hashlib
import re


@app.route('/ThreatKB/files', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_all_files():
    """Return list of a files
    Return: list of file dictionary"""
    entity_type = request.args.get("entity_type", None)
    entity_id = request.args.get("entity_id", None)

    entities = files.Files.query.filter_by(entity_type=entity_type,
                                           entity_id=entity_id).all()
    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype="application/json")


@app.route('/ThreatKB/file_upload', methods=['POST'])
@auto.doc()
@login_required
def upload_file():
    """Upload and create a file
    From Data: file (multi-part file), entity_type (int) {"SIGNATURE": 1, "DNS": 2, "IP": 3, "TASK": 4}, entity_id (int)
    Return: file status dictionary"""
    if 'file' not in request.files:
        return jsonify({})

    f = request.files['file']

    if f.filename == '':
        return jsonify({})

    files_added = {}
    files_skipped = {}
    if f:
        filename = secure_filename(f.filename)

        landing_zone_file = "%s%s%s" % (tempfile.gettempdir(), os.sep, filename)
        f.save(landing_zone_file)
        files_directory = sha1(landing_zone_file)
        full_path = files.Files.get_path_for_file(request.values['entity_type'], request.values['entity_id'],
                                                  files_directory)
        file_path = "%s%s" % (full_path, filename)

        if not os.path.exists(os.path.dirname(full_path)):
            try:
                os.makedirs(os.path.dirname(full_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        if os.path.exists(file_path):
            os.remove(file_path)

        shutil.move(landing_zone_file, file_path)

        files_added["UPLOADED"] = [filename]

        file_entity = files.Files.query.filter_by(
            entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
            entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
            filename=f.filename).first()
        if not file_entity:
            file_entity = files.Files(
                filename=f.filename,
                directory=files_directory,
                content_type=f.content_type,
                entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
                entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
                user_id=current_user.id,
                sha1=hashlib.sha1(open(file_path, 'rb').read()).hexdigest(),
                md5=hashlib.md5(open(file_path, 'rb').read()).hexdigest(),
                sha256=hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
            )
            db.session.add(file_entity)
        else:
            file_entity = files.Files(
                id=file_entity.id,
                user_id=current_user.id,
                date_modified=db.func.current_timestamp(),
                sha1=hashlib.sha1(open(file_path, 'rb').read()).hexdigest(),
                md5=hashlib.md5(open(file_path, 'rb').read()).hexdigest(),
                sha256=hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
            )
            db.session.merge(file_entity)

        ## POSTPROCESSOR FUNCTIONALITY ##
        app.logger.debug("POSTPROCESSOR STARTING")
        postprocessors = cfg_settings.Cfg_settings.get_settings("POSTPROCESSOR%")
        postprocessing_exclude_files_regex = cfg_settings.Cfg_settings.get_setting("POSTPROCESSING_EXCLUDE_FILES_REGEX")
        for postprocessor in postprocessors:
            app.logger.debug("POSTPROCESSOR STARTING '%s'" % (postprocessor.key))
            postprocessing_tempdir = cfg_settings.Cfg_settings.get_setting("POSTPROCESSING_FILE_STORE_PATH") or "/tmp"
            tempdir = "%s/%s" % (postprocessing_tempdir.rstrip(os.sep), files_directory)
            files_added[postprocessor.key] = []
            files_skipped[postprocessor.key] = []
            try:
                shutil.rmtree(tempdir)
            except Exception, e:
                pass

            try:
                os.makedirs(tempdir)
                shutil.copy(file_path, tempdir)
            except Exception, e:
                pass

            current_path = os.getcwd()
            os.chdir(tempdir)
            app.logger.debug("POSTPROCESSOR CWD is now '%s'" % (tempdir))
            app.logger.debug("POSTPROCESSOR DIRLIST is:\n\n%s" % (os.listdir(".")))
            try:
                command = "%s %s/%s %s/%s-pp" % (postprocessor.value, filename) if not "{FILENAME}" in postprocessor.value else str(
                    postprocessor.value).replace("{FILENAME}", "%s/%s" % (tempdir, filename))
                app.logger.debug("POSTPROCESSOR COMMAND '%s'" % (command))
                # proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
                # proc.wait()
                proc = delegator.run(command, env={'DOCKER_HOST': 'unix:///var/run/docker.sock'})
                stdout, stderr, return_code = proc.out, proc.err, proc.return_code
                app.logger.debug("POSTPROCESSOR STDOUT is:\n\n%s" % (stdout))
                app.logger.debug("POSTPROCESSOR STDERR is: \n\n%s" % (stderr))
                app.logger.debug("POSTPROCESSOR RETCODE is: \n\n%s" % (return_code))
            except Exception as e:
                app.logger.exception(e)

            app.logger.debug("POSTPROCESSOR DIRLIST is now:\n\n%s" % (os.listdir(".")))
            for root, dirs, files_local in os.walk(tempdir, topdown=False):
                for name in files_local:
                    current_tempfile = os.path.join(root, name)
                    app.logger.debug("POSTPROCESSOR TEMPFILE '%s'" % (current_tempfile))
                    try:
                        if name == filename:
                            app.logger.debug("Filename '%s' is the original file. Skipping." % (name))
                            continue
                        if re.search(postprocessing_exclude_files_regex, name, re.IGNORECASE):
                            app.logger.debug(
                                "Filename '%s' matched against postprocessing exclude regex of '%s'. Skipping." % (
                                    filename, postprocessing_exclude_files_regex))
                            files_skipped[postprocessor.key].append(name)
                            continue
                    except:
                        pass

                    full_path_temp = os.path.join(full_path, root.replace(tempdir, "")[1:], name)
                    if not os.path.isabs(full_path_temp):
                        full_path_temp = "%s%s%s" % (current_path, os.sep, full_path_temp)

                    if not os.path.exists(os.path.dirname(full_path_temp)):
                        os.makedirs(os.path.dirname(full_path_temp))

                    shutil.copy(current_tempfile, full_path_temp)

                    directory_for_file = os.path.dirname(full_path_temp[full_path_temp.find(files_directory):])

                    file_entity = files.Files.query.filter_by(
                        entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
                        entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
                        directory=directory_for_file,
                        filename=name).first()
                    app.logger.debug("POSTPROCESSOR FILE ENTITY '%s'" % (file_entity))
                    if not file_entity:
                        file_entity = files.Files(
                            filename=name,
                            directory=directory_for_file,
                            content_type=f.content_type,
                            entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
                            entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
                            user_id=current_user.id,
                            sha1=hashlib.sha1(open(full_path_temp, 'rb').read()).hexdigest(),
                            md5=hashlib.md5(open(full_path_temp, 'rb').read()).hexdigest(),
                            sha256=hashlib.sha256(open(full_path_temp, 'rb').read()).hexdigest()
                        )
                        db.session.add(file_entity)
                        app.logger.debug("POSTPROCESSOR FILE ADDED '%s'" % (file_entity.filename))
                        files_added[postprocessor.key].append(name)
                    else:
                        file_entity = files.Files(
                            id=file_entity.id,
                            directory=directory_for_file,
                            user_id=current_user.id,
                            date_modified=db.func.current_timestamp(),
                            sha1=hashlib.sha1(open(full_path_temp, 'rb').read()).hexdigest(),
                            md5=hashlib.md5(open(full_path_temp, 'rb').read()).hexdigest(),
                            sha256=hashlib.sha256(open(full_path_temp, 'rb').read()).hexdigest()
                        )
                        db.session.merge(file_entity)

            os.chdir(current_path)
            shutil.rmtree(tempdir)

        db.session.commit()
        return jsonify({"files_added": files_added, "files_skipped": files_skipped})

    return jsonify({})


@app.route('/ThreatKB/files/<string:entity_type>/<int:entity_id>/<int:file_id>', methods=['GET'])
@auto.doc()
@login_required
def get_file_for_entity(entity_type, entity_id, file_id):
    """Return file associated with file_id, entity_id, and entity_type
    Return: file (streamed for downloading)"""
    file_entity = files.Files.query.get(file_id)

    if not file_entity:
        abort(404)

    full_path = file_entity.get_file_path()

    if not os.path.isabs(full_path):
        full_path = "%s%s%s" % (os.getcwd(), os.sep, full_path)

    if not os.path.exists(full_path):
        abort(404, "Path not found: %s" % (full_path))

    return send_file(full_path,
                     attachment_filename="{}".format(file_entity.filename),
                     as_attachment=True)


@app.route('/ThreatKB/files/<int:file_id>', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_file(file_id):
    """Delete file associated with given file_id
    Return: None"""
    entity = files.Files.query.get(file_id)
    if not entity:
        abort(404, "File entity not found")

    full_path = entity.get_file_path()

    if os.path.exists(full_path):
        os.remove(full_path)

    db.session.delete(entity)
    db.session.commit()
    return '', 204


@app.route('/ThreatKB/files/batch/delete', methods=['PUT'])
@auto.doc()
@login_required
def batch_delete_files():
    """Batch delete files
    From Data: batch {
                 ids (array)
               }
    Return: Success Code"""

    if 'batch' in request.json and request.json['batch'] and \
            'ids' in request.json['batch'] and request.json['batch']['ids']:
        paths_of_files_to_delete = []
        for b in request.json['batch']['ids']:
            entity = files.Files.query.get(b)
            if not entity:
                abort(404)
            paths_of_files_to_delete.append(entity.get_file_path())

        for file_path in paths_of_files_to_delete:
            if os.path.exists(file_path):
                os.remove(file_path)
        db.session.execute(files.Files.__table__.delete()
                           .where(files.Files.id.in_(request.json['batch']['ids'])))
        db.session.commit()

    return jsonify(''), 200
