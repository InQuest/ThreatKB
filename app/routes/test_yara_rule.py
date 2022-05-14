

import multiprocessing
import ntpath
import os
import time
import datetime
import io
import yara
import re
import uuid
import subprocess

from sqlalchemy import func, not_, text
from sqlalchemy.ext.serializer import loads, dumps

from app import app, db, admin_only, auto
from app.celeryapp import celery
from app.models import yara_rule
from flask import abort, jsonify, request, json, Response
from flask_login import current_user, login_required

from app.models.users import KBUser
from app.models.cfg_settings import Cfg_settings
from app.models.yara_rule import Yara_testing_history, Yara_rule, Yara_testing_history_files_matches


@app.route('/ThreatKB/tests', methods=['GET'])
@auto.doc()
@login_required
def get_all_tests():
    """Return a list of all tests artifacts.

    Pagination variables:
    page_number: page number to start on, default 0
    page_size: the size of each page, default None (dont paginate)
    sort_by: column to sort by, must exist on the Yara_rule model, default None
    sort_direction: the direction to sort by if sorting, default ASC
    searches: dictionary of column filters as {column1:filter1, column2:filter2}, columns must exist on Yara_rule model, default {}

    Return: list of tests artifact dictionaries
    """
    searches = request.args.get('searches', '{}')
    page_number = request.args.get('page_number', False)
    page_size = request.args.get('page_size', False)
    sort_by = request.args.get('sort_by', False)
    sort_direction = request.args.get('sort_dir', 'ASC')

    searches = json.loads(searches)

    entity = Yara_testing_history
    entities = entity.query

    for column, value in list(searches.items()):
        if not value:
            continue

        s_value = str(value)
        l_value = "%" + s_value[1:] + "%" if s_value.startswith("!") else "%" + s_value + "%"

        if column == "yara_rule_name":
            entities = entities.join(Yara_rule, entity.yara_rule_id == Yara_rule.id) \
                .filter(not_(Yara_rule.name.like(l_value)) if s_value.startswith("!") else Yara_rule.name.like(l_value))
            continue
        elif column == "user_email":
            entities = entities.join(KBUser, entity.user_id == KBUser.id) \
                .filter(not_(KBUser.email.like(l_value)) if s_value.startswith("!") else KBUser.email.like(l_value))
            continue

        try:
            column = getattr(entity, column)
            entities = entities.filter(not_(column.like(l_value)) if s_value.startswith("!") else column.like(l_value))
        except AttributeError as e:
            pass

    filtered_entities = entities
    total_count = entities.count()

    if sort_by:
        filtered_entities = filtered_entities.order_by(text("%s %s" % (sort_by, sort_direction)))
    else:
        filtered_entities = filtered_entities.order_by(text("start_time DESC"))

    if page_size:
        filtered_entities = filtered_entities.limit(int(page_size))

    if page_number:
        filtered_entities = filtered_entities.offset(int(page_number) * int(page_size))

    filtered_entities = filtered_entities.all()

    response_dict = dict()
    response_dict['data'] = [entity.to_dict() for entity in filtered_entities]
    response_dict['total_count'] = total_count

    return json.dumps(response_dict)


@app.route('/ThreatKB/tests/create/<int:rule_id>', methods=['POST'])
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
        is_neg_test = True if is_neg_test == "1" else False
        if not is_neg_test:
            for f in yara_rule_entity.files:
                file_store_path = Cfg_settings.get_setting("FILE_STORE_PATH")
                if not file_store_path:
                    raise Exception('FILE_STORE_PATH configuration setting not set.')
                files_to_test.append(os.path.join(file_store_path,
                                                  str(f.entity_type) if f.entity_type is not None else "",
                                                  str(f.entity_id) if f.entity_id is not None else "",
                                                  str(f.filename)))
        if not is_neg_test:
            return jsonify(test_yara_rule(yara_rule_entity, files_to_test, current_user.id, False, is_neg_test)), 200
        else:
            test_yara_rule_task.delay(yara_rule_entity.id, current_user.id, is_neg_test)
            return jsonify({"status": "ok", "message": "Background job created"}), 200
    except Exception as e:
        return e.message, 500


@app.route('/ThreatKB/tests/<int:test_id>', methods=['GET'])
@auto.doc()
@login_required
def get_test_results(test_id):
    yrh = Yara_testing_history.query.get(test_id)
    return jsonify(yrh.to_dict(include_results=True)), 200


@celery.task()
def test_yara_rule_task(rule_id, user, is_neg_test):
    print("in test_yara_rule_task")
    files_to_test = []
    yara_rule_entity = yara_rule.Yara_rule.query.get(rule_id)
    if not yara_rule_entity:
        abort(500)

    print("yara rule entity %s" % (yara_rule_entity))
    neg_test_dir = Cfg_settings.get_setting("NEGATIVE_TESTING_FILE_DIRECTORY")
    if not os.path.exists(neg_test_dir):
        abort(500)

    for root_path, dirs, dir_files in os.walk(neg_test_dir):
        for f_name in dir_files:
            files_to_test.append(os.path.join(root_path, f_name))

    print("files to test %s" % (str(files_to_test)))
    return test_yara_rule(yara_rule_entity, files_to_test, user, True, is_neg_test)


def test_yara_rule(yara_rule_entity, files_to_test, user, is_async=False, is_neg_test=False):
    if type(yara_rule_entity) is int:
        yara_rule_entity = yara_rule.Yara_rule.query.get(yara_rule_entity)

    old_avg = db.session.query(func.avg(Yara_testing_history.avg_millis_per_file).label('average')) \
        .filter(Yara_testing_history.yara_rule_id == yara_rule_entity.id) \
        .scalar()

    start_time = time.time()
    start_time_str = datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')

    rule = get_yara_rule(yara_rule_entity)

    total_file_count, count_of_files_matched, tests_terminated, total_file_time, errors_encountered = 0, 0, 0, 0, 0
    error_msgs = []
    files_matches = []
    threshold = float(Cfg_settings.get_setting("MAX_MILLIS_PER_FILE_THRESHOLD") or 3.0)
    yara_command = Cfg_settings.get_setting("SIGNATURE_TESTING_COMMAND")
    yara_test_regex = Cfg_settings.get_setting("SIGNATURE_TESTING_COMMAND_SUCCESS_REGEX")

    yrh = Yara_testing_history(yara_rule_id=yara_rule_entity.id,
                               revision=yara_rule_entity.revision,
                               start_time=start_time_str,
                               end_time=None,
                               files_tested=0,
                               files_matched=0,
                               avg_millis_per_file=0,
                               total_files=len(files_to_test),
                               status=Yara_testing_history.STATUS_RUNNING,
                               test_type=Yara_testing_history.TEST_TYPE_NEGATIVE if is_neg_test else Yara_testing_history.TEST_TYPE_POSITIVE,
                               user_id=user)
    db.session.add(yrh)
    db.session.commit()

    processes = []
    manager_dicts = []
    for file_path in files_to_test:
        total_file_count += 1

        if (total_file_count % 10) == 0:
            yrh.files_tested = total_file_count
            db.session.add(yrh)
            db.session.commit()

        if not os.path.exists(file_path):
            errors_encountered += 1
            error_msgs.append(ntpath.basename(file_path) + " not in File Store Path.")
            continue

        if not is_async:
            manager = multiprocessing.Manager()
            manager_dict = manager.dict()
            if old_avg:
                p = multiprocessing.Process(target=perform_rule_match,
                                            args=(rule, file_path, manager_dict, yara_command, yara_test_regex))
                processes.append(p)
                p.start()
            else:
                perform_rule_match(rule, file_path, manager_dict, yara_command, yara_test_regex)
            manager_dicts.append(manager_dict)
        else:
            manager_dicts.append(perform_rule_match(rule, file_path, dict(), yara_command, yara_test_regex))

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
            files_matches.append(Yara_testing_history_files_matches(run_time=managers['duration'],
                                                                    path=managers['file_path'],
                                                                    stdout=managers['stdout'],
                                                                    stderr=managers['stderr'],
                                                                    command=managers['command'],
                                                                    command_match_test_regex=managers[
                                                                        'command_match_test_regex']))

    end_time = time.time()
    end_time_str = datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')

    if total_file_count > 0:
        yrh.status = Yara_testing_history.STATUS_COMPLETE
        yrh.end_time = end_time_str
        yrh.files_tested = total_file_count
        yrh.files_matched = count_of_files_matched
        yrh.avg_millis_per_file = ((total_file_time) / total_file_count)
        db.session.add(yrh)
        db.session.commit()
        for match in files_matches:
            match.history = yrh
            db.session.add(match)
        db.session.commit()

    return dict(duration=(total_file_time * 1000),
                files_tested=total_file_count,
                files_matched=count_of_files_matched,
                tests_terminated=tests_terminated,
                errors_encountered=errors_encountered,
                error_msgs=error_msgs)


def does_rule_compile(yara_dict):
    rule = Yara_rule.to_yara_rule_string(yara_dict, include_imports=True)
    rule_temp_path = "/tmp/%s.yar" % (str(uuid.uuid4()).replace("-", "")[0:8])
    with open(rule_temp_path, "w") as f:
        f.write(rule)

    yara_command = Cfg_settings.get_setting("SIGNATURE_TESTING_COMMAND")

    command = yara_command.replace("RULE", rule_temp_path).replace("FILE_PATH", rule_temp_path)
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()
    stdout, stderr = proc.communicate()
    return_code = proc.returncode
    return (return_code == 0, return_code, stdout, stderr)


def get_yara_rule(yara_rule_entity):
    rule_string = yara_rule_entity.to_dict(include_yara_rule_string=True, include_relationships=False)[
        "yara_rule_string"]
    # rule_string = """
    # rule %s
    # {
    #     strings:
    #         %s
    #     condition:
    #         %s
    # }
    # """ % (yara_rule_entity.name,
    #        yara_rule_entity.strings,
    #        yara_rule_entity.condition)

    return rule_string


def perform_rule_match(rule, file_path, manager_dict, yara_command, yara_test_regex):
    start = time.time()
    rule_temp_path = "/tmp/%s.yar" % (str(uuid.uuid4()).replace("-", ""))
    with open(rule_temp_path, "w") as f:
        f.write(rule)

    command = yara_command.replace("RULE", rule_temp_path).replace("FILE_PATH", file_path)
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()
    stdout, stderr = proc.communicate()
    end = time.time()
    manager_dict['duration'] = end - start
    manager_dict['stdout'] = stdout.decode()
    manager_dict['stderr'] = stderr.decode()
    manager_dict['file_path'] = file_path
    manager_dict['command'] = yara_command
    manager_dict['command_match_test_regex'] = yara_test_regex

    if re.search(yara_test_regex, manager_dict['stdout']):
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


if __name__ == "__main__":
    import sys

    rule = """rule hello {
        strings:
                $a1="hello"
        condition:
                any of them
}"""
    a = perform_rule_match(rule, "/Users/danny/Desktop/temp/hello.yar", multiprocessing.Manager().dict(),
                           "/usr/local/bin/yara RULE FILE_PATH", "[A-Za-z0-9]")
    sys.stdout.write(str(a))
