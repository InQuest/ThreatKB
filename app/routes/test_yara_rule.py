from __future__ import print_function
from __future__ import division
import multiprocessing
import ntpath
import os
import time
import datetime
import StringIO
import yara

from sqlalchemy import func
from sqlalchemy.ext.serializer import loads, dumps

from app import app, db, admin_only, auto
from app.celeryapp import celery
from app.models import yara_rule
from flask import abort, jsonify, request, json, Response
from flask.ext.login import current_user, login_required

from app.models.cfg_settings import Cfg_settings
from app.models.yara_rule import Yara_testing_history


@app.route('/ThreatKB/test_yara_rule/<int:rule_id>', methods=['GET'])
@auto.doc()
@login_required
def test_yara_rule_rest(rule_id):
    """Synchronously test yara rule associated with rule_id against all files attached to it
    Return: results dictionary"""
    yara_rule_entity = yara_rule.Yara_rule.query.get(rule_id)
    if not yara_rule_entity:
        abort(500)

    try:
        files_to_test = []
        is_neg_test = str(request.args.get("negative", "0"))
        if is_neg_test == "1":
            neg_test_dir = Cfg_settings.get_setting("NEGATIVE_TESTING_FILE_DIRECTORY")
            for root_path, dirs, dir_files in os.walk(neg_test_dir):
                for f_name in dir_files:
                    files_to_test.append(os.path.join(root_path, f_name))
        else:
            for f in yara_rule_entity.files:
                file_store_path = Cfg_settings.get_setting("FILE_STORE_PATH")
                if not file_store_path:
                    raise Exception('FILE_STORE_PATH configuration setting not set.')
                files_to_test.append(os.path.join(file_store_path,
                                                  str(f.entity_type) if f.entity_type is not None else "",
                                                  str(f.entity_id) if f.entity_id is not None else "",
                                                  str(f.filename)))
        return jsonify(test_yara_rule(yara_rule_entity, files_to_test, current_user.id)), 200
    except Exception as e:
        return e.message, 500


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

    total_file_count, count_of_files_matched, tests_terminated, total_file_time, errors_encountered = 0, 0, 0, 0, 0
    error_msgs = []
    threshold = float(Cfg_settings.get_private_setting("MAX_MILLIS_PER_FILE_THRESHOLD")) or 3.0
    processes = []
    manager_dicts = []
    for file_path in files_to_test:
        total_file_count += 1

        if not os.path.exists(file_path):
            errors_encountered += 1
            error_msgs.append(ntpath.basename(file_path) + " not in File Store Path.")
            continue

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

    return dict(duration=(total_file_time * 1000),
                files_tested=total_file_count,
                files_matched=count_of_files_matched,
                tests_terminated=tests_terminated,
                errors_encountered=errors_encountered,
                error_msgs=error_msgs)


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
