from app import app, db, admin_only, auto, ENTITY_MAPPING
from app.models import cfg_settings, files
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
import shutil
import magic
from sqlalchemy import or_, and_


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
        file_store_path_root = cfg_settings.Cfg_settings.get_setting("FILE_STORE_PATH") or "/tmp"
        filename = secure_filename(f.filename)
        full_path = os.path.join(file_store_path_root,
                                 request.values['entity_type'] if 'entity_type' in request.values else "",
                                 request.values['entity_id'] if 'entity_id' in request.values else "",
                                 filename)

        try:
            os.makedirs(os.path.dirname(full_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        f.save(full_path)
        sha1 = hashlib.sha1(open(full_path, 'rb').read()).hexdigest()
        md5 = hashlib.md5(open(full_path, 'rb').read()).hexdigest(),
        sha256 = hashlib.sha256(open(full_path, 'rb').read()).hexdigest()

        new_directory = os.path.join(file_store_path_root,
                                     request.values['entity_type'] if 'entity_type' in request.values else "",
                                     request.values['entity_id'] if 'entity_id' in request.values else "",
                                     sha1)

        if os.path.exists(new_directory):
            shutil.rmtree(new_directory)

        try:
            os.mkdir(new_directory)
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

        shutil.move(full_path, new_directory)
        full_path = os.path.join(new_directory, filename)

        files_added["UPLOADED"] = [filename]

        file_entity = files.Files.query.filter_by(
            entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
            entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
            sha1=sha1,
            filename=filename).first()

        if not file_entity:
            file_entity = files.Files(
                filename=f.filename,
                content_type=f.content_type,
                entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
                entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
                user_id=current_user.id,
                sha1=sha1,
                md5=md5,
                sha256=sha256
            )
            db.session.add(file_entity)
        else:
            file_entity.user_id = current_user.id
            file_entity.date_modified = db.func.current_timestamp()
            file_entity.md5 = md5
            file_entity.sha1 = sha1
            file_entity.sha256 = sha256

        parent_file = file_entity

        ## POSTPROCESSOR FUNCTIONALITY ##
        app.logger.debug("POSTPROCESSOR STARTING")
        postprocessors = cfg_settings.Cfg_settings.get_settings("POSTPROCESSOR%")
        postprocessing_exclude_files_regex = cfg_settings.Cfg_settings.get_setting("POSTPROCESSING_EXCLUDE_FILES_REGEX")
        for postprocessor in postprocessors:
            app.logger.debug("POSTPROCESSOR STARTING '%s'" % (postprocessor.key))
            postprocessing_tempdir = cfg_settings.Cfg_settings.get_setting("POSTPROCESSING_FILE_STORE_PATH") or "/tmp"
            tempdir = "%s/%s" % (postprocessing_tempdir.rstrip(os.sep), uuid.uuid4())
            files_added[postprocessor.key] = []
            files_skipped[postprocessor.key] = []
            try:
                os.makedirs(tempdir)
                shutil.copy(full_path, tempdir)
            except Exception as e:
                pass

            current_path = os.getcwd()
            os.chdir(tempdir)
            app.logger.debug("POSTPROCESSOR CWD is now '%s'" % (tempdir))
            app.logger.debug("POSTPROCESSOR DIRLIST is:\n\n%s" % (os.listdir(".")))
            try:
                # command = "%s %s/%s %s/%s-pp" % (postprocessor.value, filename) if not "{FILENAME}" in postprocessor.value else str(
                #     postprocessor.value).replace("{FILENAME}", "%s/%s" % (tempdir, filename))
                command = f"{postprocessor.value}" if not "{FILENAME}" in postprocessor.value else postprocessor.value.replace(
                    "{FILENAME}", f"{tempdir}/{filename}")
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
                    sha1 = hashlib.sha1(open(current_tempfile, 'rb').read()).hexdigest()
                    md5 = hashlib.md5(open(current_tempfile, 'rb').read()).hexdigest(),
                    sha256 = hashlib.sha256(open(current_tempfile, 'rb').read()).hexdigest()
                    path = root.replace(tempdir, "").lstrip(os.path.sep)

                    app.logger.debug("POSTPROCESSOR TEMPFILE '%s'" % (current_tempfile))
                    app.logger.debug(f"POSTPROCESSOR FILES: {root} {dirs} {files_local}")
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

                    full_path_temp = os.path.join(file_store_path_root,
                                                  request.values[
                                                      'entity_type'] if 'entity_type' in request.values else "",
                                                  request.values['entity_id'] if 'entity_id' in request.values else "",
                                                  parent_file.sha1,
                                                  path,
                                                  name)

                    if not os.path.exists(os.path.dirname(full_path_temp)):
                        try:
                            os.makedirs(os.path.dirname(full_path_temp))
                        except OSError as exc:  # Guard against race condition
                            if exc.errno != errno.EEXIST:
                                raise

                    shutil.move(current_tempfile, full_path_temp)
                    file_entity = files.Files.query.filter_by(
                        entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
                        entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
                        sha1=sha1,
                        parent_sha1=parent_file.sha1,
                        filename=name).first()
                    app.logger.debug("POSTPROCESSOR FILE ENTITY '%s'" % (file_entity))
                    mime = magic.Magic(mime=True)
                    if not file_entity:
                        file_entity = files.Files(
                            filename=name,
                            content_type=mime.from_file(full_path_temp),
                            entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
                            entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
                            user_id=current_user.id,
                            sha1=sha1,
                            md5=md5,
                            sha256=sha256,
                            parent_sha256=parent_file.sha256,
                            parent_sha1=parent_file.sha1,
                            parent_md5=parent_file.md5,
                            path=path
                        )
                        db.session.add(file_entity)
                        app.logger.debug("POSTPROCESSOR FILE ADDED '%s'" % (file_entity.filename))
                        files_added[postprocessor.key].append(name)
                    else:
                        file_entity.user_id = current_user.id
                        file_entity.content_type = mime.from_file(full_path_temp)
                        file_entity.date_modified = db.func.current_timestamp()
                        file_entity.sha1 = sha1
                        file_entity.sha256 = sha256
                        file_entity.md5 = md5
                        file_entity.path = path
                        file_entity.parent_sha256 = parent_file.sha256
                        file_entity.parent_sha1 = parent_file.sha1
                        file_entity.parenty_md5 = parent_file.md5

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

    full_path = os.path.join(file_entity.full_path,
                             secure_filename(file_entity.filename))
    if not os.path.exists(full_path):
        abort(404)

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
        abort(404)

    if request.args.get("path", False) and request.args.get("path") == "1":

        if entity.is_parent_file:
            db.session.query(files.Files).filter(files.Files.parent_sha1 == entity.sha1).delete()
        else:
            db.session.query(files.Files).filter(files.Files.parent_sha1 == entity.parent_sha1).filter(
                files.Files.path.like(f"{entity.path}%")).delete(synchronize_session=False)
        db.session.delete(entity)
        db.session.commit()

        if os.path.exists(entity.full_path):
            shutil.rmtree(entity.full_path)

        return '', 204

    else:
        full_path = os.path.join(app.config['FILE_STORE_PATH'],
                                 str(entity.entity_type) if entity.entity_type else "",
                                 str(entity.entity_id) if entity.entity_id else "",
                                 secure_filename(entity.filename))
        if os.path.exists(full_path):
            os.remove(full_path)

        db.session.delete(entity)
        db.session.commit()
        return '', 204
