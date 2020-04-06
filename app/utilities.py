import distutils
import re
import json
import sys
import hashlib

from flask_login import current_user
from plyara import Plyara

from more_itertools import unique_everseen
from sqlalchemy import and_, not_, or_

from app import ENTITY_MAPPING
from app.models import cfg_settings
from app.models.comments import Comments
from app.models.c2dns import C2dns
from app.models.c2ip import C2ip
from app.models.metadata import Metadata, MetadataMapping
from app.models.tags_mapping import Tags_mapping
from app.models.tags import Tags
from app.models.users import KBUser
from app.models.yara_rule import Yara_rule

# Appears that Ply needs to read the source, so disable bytecode.
sys.dont_write_bytecode


#####################################################################

def extract_ips_text(text):
    regex = cfg_settings.Cfg_settings.get_setting(key="IMPORT_IP_REGEX")
    ip_regex = regex if regex else '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:\/\d{1,3})?)'
    return re.compile(ip_regex).findall(text.replace("[.]", "."))


#####################################################################

def extract_dns_text(text):
    hostnames = []
    regex = cfg_settings.Cfg_settings.get_setting(key="IMPORT_DNS_REGEX")
    url_regex = regex if regex else 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    for dns in re.compile(url_regex).findall(text.replace("[.]", ".")):
        try:
            hostnames.append(dns)
        except:
            pass
    return hostnames


#####################################################################

def extract_yara_rules_text(text):
    imports = Yara_rule.get_imports_from_string(text)
    split_regex = cfg_settings.Cfg_settings.get_setting(key="IMPORT_SIG_SPLIT_REGEX")
    split_regex = split_regex if split_regex else "\n[\t\s]*\}[\s\t]*(rule[\t\s][^\r\n]+(?:\{|[\r\n][\r\n\s\t]*\{))"
    parse_regex = cfg_settings.Cfg_settings.get_setting(key="IMPORT_SIG_PARSE_REGEX")
    parse_regex = parse_regex if parse_regex else r"^[\t\s]*rule[\t\s][^\r\n]+(?:\{|[\r\n][\r\n\s\t]*\{).*?condition:.*?\r?\n?[\t\s]*\}[\s\t]*(?:$|\r?\n)"

    yara_rules = re.sub(split_regex, "\n}\n\\1", text, re.MULTILINE | re.DOTALL)
    yara_rules = re.compile(parse_regex, re.MULTILINE | re.DOTALL).findall(yara_rules)
    extracted = []
    for yara_rule_original in yara_rules:
        try:
            parsed_rule = parse_yara_rules_text(yara_rule_original.strip())[0]

            strings, condition = get_strings_and_conditions(yara_rule_original)
            extracted.append(
                {"parsed_rule": parsed_rule, "strings": strings, "condition": condition, "imports": imports})
        except Exception as e:
            pass

    return extracted


#####################################################################

def filter_entities(entity,
                    artifact_type,
                    searches,
                    page_number,
                    page_size,
                    sort_by,
                    sort_direction,
                    include_metadata,
                    include_tags,
                    include_comments,
                    exclude_totals,
                    default_sort,
                    include_inactive=False,
                    include_active=True,
                    include_merged=False,
                    include_yara_string=None,
                    short=None,
                    operator="and",
                    since=None):
    searches = json.loads(searches)

    operator = and_ if operator == "and" else or_

    clauses = []

    if searches and any([search_key not in entity.__table__.columns.keys()
                         and search_key not in ("tags", "owner_user.email", "user.email")
                         for search_key, val in searches.items()]):
        entities = entity.query.outerjoin(Metadata, Metadata.artifact_type == artifact_type).join(
            MetadataMapping, and_(MetadataMapping.metadata_id == Metadata.id, MetadataMapping.artifact_id == entity.id))
    else:
        entities = entity.query

    if artifact_type == ENTITY_MAPPING["TASK"]:
        show_for_non_admin = cfg_settings.Cfg_settings.get_setting("ENABLE_NON_ADMIN_TASK_VISIBILITY")
        show_for_non_admin = bool(distutils.util.strtobool(show_for_non_admin)) if show_for_non_admin else False

        if not (show_for_non_admin or current_user.admin):
            entities = entities.filter(or_(entity.owner_user_id == current_user.id, entity.owner_user_id == None))
    elif not current_user.admin:
        entities = entities.filter_by(owner_user_id=current_user.id)

    if include_inactive and not include_active and hasattr(entity, "active"):
        entities = entities.filter_by(active=False)
    elif not include_inactive and include_active and hasattr(entity, "active"):
        entities = entities.filter_by(active=True)

    for column, value in searches.items():
        if not value:
            continue

        s_value = str(value)
        is_null = False
        if s_value == "~":
            is_null = True
        l_value = "%" + s_value[1:] + "%" if s_value.startswith("!") else "%" + s_value + "%"

        if column == "owner_user.email":
            if is_null:
                entities = entities.filter(entity.owner_user_id.is_(None))
            else:
                entities = entities.join(KBUser, entity.owner_user_id == KBUser.id) \
                    .filter(not_(KBUser.email.like(l_value)) if s_value.startswith("!") else KBUser.email.like(l_value))
            continue
        elif column == "user.email":
            if is_null:
                entities = entities.filter(entity.user_id.is_(None))
            else:
                entities = entities.join(KBUser, entity.user_id == KBUser.id) \
                    .filter(not_(KBUser.email.like(l_value)) if s_value.startswith("!") else KBUser.email.like(l_value))
            continue
        elif column == "comments":
            if is_null:
                entities = entities.filter(Comments.comment.is_(None))
            else:
                entities = entities \
                    .join(Comments, and_(Comments.entity_type == artifact_type, Comments.entity_id == entity.id)) \
                    .filter(not_(Comments.comment.like(l_value)
                                 if s_value.startswith("!")
                                 else Comments.comment.like(l_value)))

        if column == "tags":
            if is_null:
                entities = entities \
                    .outerjoin(Tags_mapping,
                               and_(entity.id == Tags_mapping.source_id,
                                    entity.__tablename__ == Tags_mapping.source_table)) \
                    .filter(Tags_mapping.tag_id.is_(None))
            else:
                entities = entities.outerjoin(Tags_mapping, entity.id == Tags_mapping.source_id) \
                    .filter(Tags_mapping.source_table == entity.__tablename__) \
                    .join(Tags, Tags_mapping.tag_id == Tags.id) \
                    .filter(not_(Tags.text.like(l_value)) if s_value.startswith("!") else Tags.text.like(l_value))
            continue

        try:
            column = getattr(entity, column)
            if is_null:
                clauses.append(column.is_(None))
            else:
                clauses.append(not_(column.like(l_value)) if s_value.startswith("!") else column.like(l_value))
        except AttributeError as e:
            if is_null:
                clauses.append(and_(MetadataMapping.artifact_id == entity.id, Metadata.key == column,
                                    MetadataMapping.value.is_(None)))
            else:
                clauses.append(and_(MetadataMapping.artifact_id == entity.id, Metadata.key == column,
                                    not_(MetadataMapping.value.like(l_value))
                                    if s_value.startswith("!") else MetadataMapping.value.like(l_value)))

    if since:
        try:
            clauses.append(entity.activity_date > since)
        except:
            pass

        try:
            clauses.append(entity.creation_date > since)
        except:
            pass

    if not include_merged:
        entities = entities.filter(entity.state != 'Merged')

    entities = entities.filter(operator(*clauses))
    filtered_entities = entities
    total_count = entities.count()

    if sort_by:
        filtered_entities = filtered_entities.order_by("%s %s" % (sort_by, sort_direction))
    else:
        filtered_entities = filtered_entities.order_by("%s DESC" % default_sort)

    if page_size:
        filtered_entities = filtered_entities.limit(int(page_size))

    if page_number:
        filtered_entities = filtered_entities.offset(int(page_number) * int(page_size))

    filtered_entities = filtered_entities.all()

    response_dict = dict()
    if artifact_type == "ACTIVITY_LOG":
        response_dict['data'] = [entity.to_dict() for entity in filtered_entities]
    elif artifact_type == ENTITY_MAPPING["TASK"]:
        response_dict['data'] = [entity.to_dict(include_comments=include_comments) for entity in filtered_entities]
    elif artifact_type == ENTITY_MAPPING["SIGNATURE"]:
        response_dict['data'] = [
            entity.to_dict(include_yara_rule_string=include_yara_string, short=short, include_metadata=include_metadata)
            for entity in filtered_entities]
    else:
        response_dict['data'] = [entity.to_dict(include_metadata=include_metadata, include_comments=include_comments,
                                                include_tags=include_tags) for entity in filtered_entities]
    response_dict['total_count'] = total_count

    if exclude_totals:
        return json.dumps(response_dict['data'])
    else:
        return json.dumps(response_dict)


#####################################################################

def get_strings_and_conditions(rule):
    segment_headers = \
        {
            "strings": "^\s*strings:\s*\r?\n?",
            "condition": "^\s*condition:\s*\r?\n?",
        }
    segments = \
        {
            "strings": [],
            "condition": [],
        }
    SEGMENT = None
    for line in rule.splitlines():
        segment_change = False
        for header, rx in segment_headers.items():
            if re.match(rx, line):
                SEGMENT = header
                segment_change = True
        if SEGMENT and not segment_change:
            segments[SEGMENT].append(line)

    if segments.get("strings", None):
        segments["strings"][-1] = segments["strings"][-1].rstrip(" }") if not "=" in segments["strings"][-1] else \
            segments["strings"][-1]

    if segments.get("condition", None):
        segments["condition"][-1] = segments["condition"][-1].rstrip(" }")

    return "\n".join(segments["strings"]) if segments.get("strings", None) else "", "\n".join(segments["condition"])


#####################################################################

def extract_artifacts_by_type(type_, import_objects):
    table_mapping = {"ip": C2ip, "domain_name": C2dns}
    output = []
    processed = set()

    for import_object in import_objects:
        if import_object[type_] in processed:
            continue

        processed.add(import_object[type_])
        temp_object = {"type": type_, "metadata": {}, "artifact": import_object[type_]}
        for key, val in import_object.iteritems():
            if key.lower() == type_ or key.lower() == "artifact":
                continue
            elif key in table_mapping[type_].__table__.columns.keys():
                temp_object[key] = val
            else:
                temp_object["metadata"][key] = val

        output.append(temp_object)

    return output


#####################################################################

def extract_artifacts_json(do_extract_ip, do_extract_dns, do_extract_signature, import_objects):
    ips = extract_artifacts_by_type("ip", [import_object for import_object in import_objects if "ip" in import_object])
    dns = extract_artifacts_by_type("domain_name", [import_object for import_object in import_objects if
                                                    "domain_name" in import_object])
    temp = []
    output = []

    if do_extract_ip:
        output.extend(ips)
    if do_extract_dns:
        output.extend(dns)

    return output


#####################################################################

def extract_artifacts_text(do_extract_ip, do_extract_dns, do_extract_signature, text):
    ips = extract_ips_text(text)
    dns = extract_dns_text(text)
    yara_rules = extract_yara_rules_text(text)
    temp = []
    output = []

    if do_extract_ip:
        output.extend([{"type": "IP", "artifact": ip} for ip in list(unique_everseen(ips))])
    if do_extract_dns:
        output.extend([{"type": "DNS", "artifact": hostname} for hostname in list(unique_everseen(dns))])
    if do_extract_signature:
        for yara_rule in yara_rules:
            yr = yara_rule["parsed_rule"]  # hacky
            if not yr["rule_name"] in temp:
                temp.append(yr["rule_name"])
                output.append(
                    {"type": "YARA_RULE", "artifact": yr["rule_name"], "rule": yr, "strings": yara_rule["strings"],
                     "condition": yara_rule["condition"], "imports": yara_rule["imports"]})

    return output


#####################################################################

def extract_artifacts(do_extract_ip, do_extract_dns, do_extract_signature, text):
    try:
        import_objects = json.loads(str(text).encode("string_escape"))
        return extract_artifacts_json(do_extract_ip, do_extract_dns, do_extract_signature, import_objects)
    except ValueError as e:
        try:
            import_objects = json.loads(str(text))
            return extract_artifacts_json(do_extract_ip, do_extract_dns, do_extract_signature, import_objects)
        except ValueError as e:
            return extract_artifacts_text(do_extract_ip, do_extract_dns, do_extract_signature, text)


#####################################################################

def parse_yara_rules_file(filename):
    return parse_yara_rules_text(open(filename, "r").read())


#####################################################################

def parse_yara_rules_text(text):
    return Plyara().parse_string(text)

#####################################################################

def chunks (l, n):
    """
    Yield successive n-sized chunks from l.
    @type  l: list
    @param l: List we wish to chunk
    @type  n: int
    @param n: Chunk sizes to break l into.
    @rtype: generator.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def hash_gen (path=None, bytes=None, algorithm="md5", block_size=16384, fmt="digest"):
    """
    Return the selected algorithms crytographic hash hex digest of the given file.
    @type  path:       str
    @param path:       Path to file to hash or None if supplying bytes.
    @type  bytes:      str
    @param bytes:      str bytes to hash or None if supplying a path to a file.
    @type  algorithm:  str
    @param algorithm:  One of "md5", "sha1", "sha256" or "sha512".
    @type  block_size: int
    @param block_size: Size of blocks to process.
    @type  fmt:        str
    @param fmt:        One of "digest" (str), "raw" (hashlib object), "parts" (array of numeric parts).
    @rtype:  str
    @return: Hash as hex digest.
    """
    algorithm = algorithm.lower()
    if   algorithm == "md5":    hashfunc = hashlib.md5()
    elif algorithm == "sha1":   hashfunc = hashlib.sha1()
    elif algorithm == "sha256": hashfunc = hashlib.sha256()
    elif algorithm == "sha512": hashfunc = hashlib.sha512()
    # hash a file.
    if path:
        with open(path, "rb") as fh:
            while 1:
                data = fh.read(block_size)
                if not data:
                    break
                hashfunc.update(data)
    # hash a stream of bytes.
    elif bytes:
        hashfunc.update(bytes)
    # error.
    else:
        raise Exception("hash expects either 'path' or 'bytes'.")
    # return multiplexor.
    if fmt == "raw":
        return hashfunc
    elif fmt == "parts":
        return map(lambda x: int(x, 16), list(chunks(hashfunc.hexdigest(), 8)))
    else: # digest
        return hashfunc.hexdigest()

def md5    (path=None, bytes=None): return hash_gen(path=path, bytes=bytes, algorithm="md5")
def sha1   (path=None, bytes=None): return hash_gen(path=path, bytes=bytes, algorithm="sha1")
def sha256 (path=None, bytes=None): return hash_gen(path=path, bytes=bytes, algorithm="sha256")
def sha512 (path=None, bytes=None): return hash_gen(path=path, bytes=bytes, algorithm="sha512")
