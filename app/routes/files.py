from app import app, db, admin_only, auto
from app.models import files, cfg_settings
from flask import abort, jsonify, request, send_file, json, Response
from flask.ext.login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import errno


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
        return jsonify(fileStatus=False)

    f = request.files['file']

    if f.filename == '':
        return jsonify(fileStatus=False)

    if f:
        if request.values['entity_type'] == files.Files.ENTITY_MAPPING["CLEAN"]:
            file_store_path_root = cfg_settings.Cfg_settings.get_setting("CLEAN_FILES_CORPUS_DIRECTORY") or "/tmp"
        else:
            file_store_path_root = cfg_settings.Cfg_settings.get_setting("FILE_STORE_PATH") or "/tmp"
        filename = secure_filename(f.filename)
        full_path = os.path.join(file_store_path_root,
                                 request.values['entity_type']
                                 if request.values['entity_type'] != files.Files.ENTITY_MAPPING["CLEAN"] else "",
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
                user_id=current_user.id
            )
            db.session.add(file_entity)
        else:
            file_entity = files.Files(
                id=file_entity.id,
                user_id=current_user.id,
                date_modified=db.func.current_timestamp()
            )
            db.session.merge(file_entity)

        db.session.commit()
        return jsonify(fileStatus=True)

    return jsonify(fileStatus=False)


@app.route('/ThreatKB/files/<string:entity_type>/<int:entity_id>/<int:file_id>', methods=['GET'])
@auto.doc()
@login_required
def get_file_for_entity(entity_type, entity_id, file_id):
    """Return file associated with file_id, entity_id, and entity_type
    Return: file (streamed for downloading)"""
    file_entity = files.Files.query.get(file_id)

    if not file_entity:
        abort(404)

    if entity_type == "CLEAN":
        file_store_path = cfg_settings.Cfg_settings.get_setting("CLEAN_FILES_CORPUS_DIRECTORY") or "/tmp"
    else:
        file_store_path = cfg_settings.Cfg_settings.get_setting("FILE_STORE_PATH") or "/tmp"
    full_path = os.path.join(file_store_path,
                             str(files.Files.ENTITY_MAPPING[entity_type]) if entity_type != "CLEAN" else "",
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
