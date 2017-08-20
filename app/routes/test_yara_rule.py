import os
import time
import datetime
import StringIO
import yara

from app import app, db
from app.models import yara_rule
from flask import abort, jsonify, request
from flask.ext.login import current_user, login_required


@app.route('/InquestKB/test_yara_rule/<int:rule_id>', methods=['GET'])
@login_required
def test_yara_rule(rule_id):
    yara_rule_entity = yara_rule.Yara_rule.query.get(rule_id)
    if not yara_rule_entity:
        abort(404)

    start_time = time.time()
    start_time_str = datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')

    rule_string = """
rule %s
{
    strings:
        %s
    condition:
        %s
}
""" % (yara_rule_entity.name,
       yara_rule_entity.strings,
       yara_rule_entity.condition)

    rule_buffer = StringIO.StringIO()

    compiled_rule = yara.compile(source=rule_string)
    compiled_rule.save(file=rule_buffer)

    rule_buffer.seek(0)
    rule = yara.load(file=rule_buffer)

    total_file_count = 0
    count_of_files_matched = 0
    for f in yara_rule_entity.files:
        total_file_count += 1
        file_path = os.path.join(app.config['FILE_STORE_PATH'],
                                 str(f.entity_type),
                                 str(f.entity_id),
                                 str(f.filename))
        matches = rule.match(file_path)
        if matches and matches.__sizeof__() > 0:
            count_of_files_matched += 1

    end_time = time.time()
    end_time_str = datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')

    if total_file_count > 0:
        db.session.add(yara_rule.Yara_testing_history(yara_rule_id=yara_rule_entity.id,
                                                      revision=yara_rule_entity.revision,
                                                      start_time=start_time_str,
                                                      end_time=end_time_str,
                                                      files_tested=total_file_count,
                                                      files_matched=count_of_files_matched,
                                                      user_id=current_user.id))
        db.session.commit()

    return '', 200
