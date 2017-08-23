import os

import errno
from flask import abort, jsonify, request, send_file, json
from flask.ext.login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from app.models import files


@app.route('/InquestKB/files', methods=['GET'])
@login_required
def get_all_files():
    entity_type = request.args.get("entity_type", None)
    entity_id = request.args.get("entity_id", None)

    entities = files.Files.query.filter_by(entity_type=entity_type,
                                           entity_id=entity_id).all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/file_upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify(fileStatus=False)

    f = request.files['file']

    if f.filename == '':
        return jsonify(fileStatus=False)

    if f:
        filename = secure_filename(f.filename)
        full_path = os.path.join(app.config['FILE_STORE_PATH'],
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


@app.route('/InquestKB/files/<string:entity_type>/<int:entity_id>/<int:file_id>', methods=['GET'])
@login_required
def get_file_for_entity(entity_type, entity_id, file_id):
    file_entity = files.Files.query.get(file_id)

    if not file_entity:
        abort(404)

    full_path = os.path.join(app.config['FILE_STORE_PATH'],
                             str(files.Files.ENTITY_MAPPING[entity_type]) if entity_type != "0" else "",
                             str(entity_id) if entity_id != 0 else "",
                             secure_filename(file_entity.filename))
    if not os.path.exists(full_path):
        abort(404)

    return send_file(full_path,
                     attachment_filename="{}".format(file_entity.filename),
                     as_attachment=True)


@app.route('/InquestKB/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
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
