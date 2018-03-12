from app import app, db, admin_only, auto, ENTITY_MAPPING
from app.models import cfg_settings, files
from flask import abort, jsonify, request, send_file, json, Response
from flask.ext.login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import errno
import tempfile
import uuid
import shutil
import subprocess
import hashlib


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
    if f:
        file_store_path_root = cfg_settings.Cfg_settings.get_setting("FILE_STORE_PATH") or "/tmp"
        filename = secure_filename(f.filename)
        full_path = os.path.join(file_store_path_root,
                                 request.values['entity_type'] if 'entity_type' in request.values else "",
                                 request.values['entity_id'] if 'entity_id' in request.values else "",
                                 filename)
        if not os.path.exists(os.path.dirname(full_path)):
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
        files_added["UPLOADED"] = [filename]

        file_entity = files.Files.query.filter_by(
            entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
            entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
            filename=f.filename).first()
        if not file_entity:
            file_entity = files.Files(
                filename=f.filename,
                content_type=f.content_type,
                entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
                entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
                user_id=current_user.id,
                sha1=hashlib.sha1(open(full_path, 'rb').read()).hexdigest(),
                md5=hashlib.md5(open(full_path, 'rb').read()).hexdigest(),
                sha256=hashlib.sha256(open(full_path, 'rb').read()).hexdigest()
            )
            db.session.add(file_entity)
        else:
            file_entity = files.Files(
                id=file_entity.id,
                user_id=current_user.id,
                date_modified=db.func.current_timestamp(),
                sha1=hashlib.sha1(open(full_path, 'rb').read()).hexdigest(),
                md5=hashlib.md5(open(full_path, 'rb').read()).hexdigest(),
                sha256=hashlib.sha256(open(full_path, 'rb').read()).hexdigest()
            )
            db.session.merge(file_entity)

        ## POSTPROCESSOR FUNCTIONALITY ##
        app.logger.debug("POSTPROCESSOR STARTING")
        postprocessors = cfg_settings.Cfg_settings.get_settings("POSTPROCESSOR%")
        for postprocessor in postprocessors:
            app.logger.debug("POSTPROCESSOR STARTING '%s'" % (postprocessor.key))
            postprocessing_tempdir = cfg_settings.Cfg_settings.get_setting("POSTPROCESSING_FILE_STORE_PATH") or "/tmp"
            tempdir = "%s/%s" % (postprocessing_tempdir.rstrip(os.sep), uuid.uuid4())
            files_added[postprocessor.key] = []
            try:
                os.makedirs(tempdir)
                shutil.copy(full_path, tempdir)
            except Exception, e:
                pass

            current_path = os.getcwd()
            os.chdir(tempdir)
            app.logger.debug("POSTPROCESSOR CWD is now '%s'" % (tempdir))
            app.logger.debug("POSTPROCESSOR DIRLIST is:\n\n%s" % (os.listdir()))
            try:
                command = "%s %s" % (postprocessor.value, filename) if not "{FILENAME}" in postprocessor.value else str(
                    postprocessor.value).replace("{FILENAME}", filename)
                app.logger.debug("POSTPROCESSOR COMMAND '%s'" % (command))
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
                proc.wait()
                stdout, stderr = proc.communicate()
                app.log.debug("POSTPROCESSOR STDOUT is:\n\n%s" % (stdout))
                app.log.debug("POSTPROCESSOR STDERR is: \n\n%s" % (stderr))
            except Exception, e:
                pass

            app.logger.debug("POSTPROCESSOR DIRLIST is now:\n\n%s" % (os.listdir()))
            for root, dirs, files_local in os.walk(tempdir, topdown=False):
                for name in files_local:
                    current_tempfile = os.path.join(root, name)
                    app.logger.debug("POSTPROCESSOR TEMPFILE '%s'" % (current_tempfile))
                    if name == filename:
                        continue

                    full_path_temp = os.path.join(file_store_path_root,
                                                  request.values[
                                                      'entity_type'] if 'entity_type' in request.values else "",
                                                  request.values['entity_id'] if 'entity_id' in request.values else "",
                                                  name)
                    shutil.copy(current_tempfile, full_path_temp)
                    file_entity = files.Files.query.filter_by(
                        entity_type=(request.values['entity_type'] if 'entity_type' in request.values else None),
                        entity_id=(request.values['entity_id'] if 'entity_id' in request.values else None),
                        filename=name).first()
                    app.logger.debug("POSTPROCESSOR FILE ENTITY '%s'" % (file_entity))
                    if not file_entity:
                        file_entity = files.Files(
                            filename=name,
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
        return jsonify(files_added)

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

    full_path = os.path.join(cfg_settings.Cfg_settings.get_setting("FILE_STORE_PATH"),
                             str(ENTITY_MAPPING[entity_type]) if entity_type != "0" else "",
                             str(entity_id) if entity_id != 0 else "",
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

    full_path = os.path.join(app.config['FILE_STORE_PATH'],
                             entity.entity_type if entity.entity_type else "",
                             entity.entity_id if entity.entity_id else "",
                             secure_filename(entity.filename))
    if os.path.exists(full_path):
        os.remove(full_path)

    db.session.delete(entity)
    db.session.commit()
    return '', 204
