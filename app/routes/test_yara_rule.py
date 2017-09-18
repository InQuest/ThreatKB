from __future__ import division
import multiprocessing
import os
import time
import datetime
import StringIO
import yara

from sqlalchemy import func
from sqlalchemy.ext.serializer import loads, dumps

from app import app, db, celery, admin_only, auto
from app.models import yara_rule, files
from flask import abort, jsonify, request, json
from flask.ext.login import current_user, login_required

from app.models.yara_rule import Yara_testing_history


@app.route('/ThreatKB/test_yara_rule', methods=['POST'])
@auto.doc()
@login_required
@admin_only()
def clean_yara_test():
    """Create asynchronous testing tasks for sig_ids against all files matching pattern
     From Data: sig_ids (list of ints), pattern (str)
     Return: list of result dictionaries"""
    pattern = request.values['pattern'] if 'pattern' in request.values else ".*"
    sig_ids = json.loads(request.values['sig_ids']) if 'sig_ids' in request.values else []

    if sig_ids.__len__() == 0:
        sig_ids = get_all_sig_ids()

    results = []
    for rule_id in sig_ids:
        yara_rule_entity = yara_rule.Yara_rule.query.get(rule_id)
        if not yara_rule_entity:
            results.append(dict(sig_id=rule_id,
                                error="Error encountered"))
        else:
            file_entities = files.Files.query \
                .filter_by(entity_type=None, entity_id=None) \
                .filter(files.Files.filename.op('regexp')(r'%s' % pattern)) \
                .all()

            test_yara_rule_task.delay(yara_rule_entity.id, dumps(file_entities), current_user.id)

    return json.dumps(results), 200


@app.route('/ThreatKB/test_yara_rule/<int:rule_id>', methods=['GET'])
@auto.doc()
@login_required
def test_yara_rule_rest(rule_id):
    """Synchronously test yara rule associated with rule_id against all files attached to it
    Return: results dictionary"""
    yara_rule_entity = yara_rule.Yara_rule.query.get(rule_id)
    if not yara_rule_entity:
        abort(500)
    return jsonify(test_yara_rule(yara_rule_entity, yara_rule_entity.files, current_user.id)), 200


@celery.task()
def test_yara_rule_task(rule_id, files_to_test, user):
    yara_rule_entity = yara_rule.Yara_rule.query.get(rule_id)
    if not yara_rule_entity:
        abort(500)
    return test_yara_rule(yara_rule_entity, loads(files_to_test), user, True)


def test_yara_rule(yara_rule_entity, files_to_test, user, is_async=False):
    old_avg = db.session.query(func.avg(Yara_testing_history.avg_millis_per_file).label('average')) \
        .filter(Yara_testing_history.yara_rule_id == yara_rule_entity.id) \
        .scalar()

    start_time = time.time()
    start_time_str = datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')

    rule = get_yara_rule(yara_rule_entity)

    total_file_count, count_of_files_matched, tests_terminated, total_file_time = 0, 0, 0, 0
    threshold = app.config['MAX_MILLIS_PER_FILE_THRESHOLD']
    processes = []
    manager_dicts = []
    for f in files_to_test:
        total_file_count += 1
        file_path = os.path.join(app.config['FILE_STORE_PATH'],
                                 str(f.entity_type) if f.entity_type is not None else "",
                                 str(f.entity_id) if f.entity_id is not None else "",
                                 str(f.filename))

        if not is_async:
            manager = multiprocessing.Manager()
            manager_dict = manager.dict()
            if old_avg:
                p = multiprocessing.Process(target=perform_rule_match, args=(rule, file_path, manager_dict))
                processes.append(p)
                p.start()
            else:
                perform_rule_match(rule, file_path, manager_dict)
            manager_dicts.append(manager_dict)
        else:
            manager_dicts.append(perform_rule_match(rule, file_path, dict()))

    if old_avg and not is_async:
        time.sleep((old_avg * threshold) / 1000.0)
        for p in processes:
            p.join()

            if p.is_alive():
                tests_terminated += 1
                p.terminate()
                p.join()

    for managers in manager_dicts:
        if managers['duration']:
            total_file_time += managers['duration']
        if managers['match']:
            count_of_files_matched += 1

    end_time = time.time()
    end_time_str = datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')

    if total_file_count > 0:
        db.session.add(Yara_testing_history(yara_rule_id=yara_rule_entity.id,
                                            revision=yara_rule_entity.revision,
                                            start_time=start_time_str,
                                            end_time=end_time_str,
                                            files_tested=total_file_count,
                                            files_matched=count_of_files_matched,
                                            avg_millis_per_file=((total_file_time / total_file_count) * 1000),
                                            user_id=user))
        db.session.commit()

    return dict(files_tested=total_file_count,
                files_matched=count_of_files_matched,
                tests_terminated=tests_terminated)


def get_yara_rule(yara_rule_entity):
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
    return yara.load(file=rule_buffer)


def perform_rule_match(rule, file_path, manager_dict):
    start = time.time()
    matches = rule.match(file_path)
    end = time.time()
    manager_dict['duration'] = end - start

    if matches and matches.__sizeof__() > 0:
        manager_dict['match'] = True
    else:
        manager_dict['match'] = False
    return manager_dict


def get_all_sig_ids():
    sig_ids = []
    yara_rules = yara_rule.Yara_rule.query.all()
    for rule in yara_rules:
        sig_ids.append(rule.id)

    return sig_ids
