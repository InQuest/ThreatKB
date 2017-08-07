import os
from StringIO import StringIO
from bz2 import decompress

from flask import abort, jsonify, request, send_file, json
from flask import send_from_directory
from flask.ext.login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from app.models import files

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/InquestKB/files', methods=['GET'])
@login_required
def get_all_comments():
    entity_type = request.args.get("entity_type", None)
    entity_id = request.args.get("entity_id", None)
    entities = files.Files.query
    if entity_type:
        entities = entities.filter_by(entity_type=entity_type)
    if entity_id:
        entities = entities.filter_by(entity_id=entity_id)

    entities = entities.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/file_upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify(fileStatus=False)

    f = request.files['file']

    if f.filename == '':
        return jsonify(fileStatus=False)

    if f and allowed_file(f.filename):
        filename = secure_filename(f.filename)
        full_path = os.path.join("/tmp/", filename)
        f.save(full_path)
        opened_file = open(full_path, 'r')
        file_content = opened_file.read()
        opened_file.close()

        file_entity = files.Files(
            file=file_content,
            filename=f.filename,
            content_type=f.content_type,
            entity_type=request.values['entity_type'],
            entity_id=request.values['entity_id'],
            user_id=current_user.id
        )
        db.session.add(file_entity)
        db.session.commit()
        return jsonify(fileStatus=True)

    return jsonify(fileStatus=False)


@app.route('/InquestKB/files/<filename>')
def uploaded_file(filename):
    return send_from_directory("/tmp/", filename)


@app.route('/InquestKB/files/<int:file_id>', methods=['GET'])
@login_required
def get_file(file_id):
    f = files.Files.query.get(file_id)

    if not f:
        abort(404)

    ff = decompress(f.file)
    sio = StringIO()
    sio.write(ff)
    sio.seek(0)
    return send_file(sio, attachment_filename="{}".format(f.filename), as_attachment=True)
