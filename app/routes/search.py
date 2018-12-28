from flask import request, Response, json, abort
from flask_login import login_required
from sqlalchemy import or_, and_
from app import app, db, auto, ENTITY_MAPPING
from app.models import yara_rule, c2dns, c2ip, tasks, tags, tags_mapping, metadata
import json


@app.route('/ThreatKB/search', methods=['GET'])
@auto.doc()
def do_search():
    """Returns list of artifacts based on the search criteria.
    From Data: tag (str), state (str), category (str), description (str), artifact_type (comma-separated list of dns, ip, signature, task)
    Return: dictionary of lists of artifact dictionaries"""
    tag = request.args.get("tag", None)
    state = request.args.get('state', None)
    all = request.args.get("all", None)
    artifact_type = request.args.get('artifact_type', None)
    category = request.args.get('category', None)

    if not tag and not state and not category and not artifact_type and not all:
        abort(400)

    if artifact_type:
        artifact_type = [a.lower() for a in artifact_type.split(",")]

    results = {"tasks": [], "ips": [], "dns": [], "signatures": []}

    signatures = yara_rule.Yara_rule.query
    ips = c2ip.C2ip.query
    dns = c2dns.C2dns.query
    task = tasks.Tasks.query

    if tag:
        signatures = db.session.query(yara_rule.Yara_rule).join(tags_mapping.Tags_mapping,
                                                                tags_mapping.Tags_mapping.source_id == yara_rule.Yara_rule.id).join(
            tags.Tags, tags.Tags.id == tags_mapping.Tags_mapping.tag_id).filter_by(text=tag).filter(
            tags_mapping.Tags_mapping.source_table == "yara_rules")
        ips = db.session.query(c2ip.C2ip).join(tags_mapping.Tags_mapping,
                                               tags_mapping.Tags_mapping.source_id == c2ip.C2ip.id).join(
            tags.Tags, tags.Tags.id == tags_mapping.Tags_mapping.tag_id).filter_by(text=tag).filter(
            tags_mapping.Tags_mapping.source_table == "c2ip")
        dns = db.session.query(c2dns.C2dns).join(tags_mapping.Tags_mapping,
                                                 tags_mapping.Tags_mapping.source_id == c2dns.C2dns.id).join(
            tags.Tags, tags.Tags.id == tags_mapping.Tags_mapping.tag_id).filter_by(text=tag).filter(
            tags_mapping.Tags_mapping.source_table == "c2dns")
        task = db.session.query(tasks.Tasks).join(tags_mapping.Tags_mapping,
                                                  tags_mapping.Tags_mapping.source_id == tasks.Tasks.id).join(
            tags.Tags, tags.Tags.id == tags_mapping.Tags_mapping.tag_id).filter_by(text=tag).filter(
            tags_mapping.Tags_mapping.source_table == "tasks")

    if state:
        signatures = signatures.filter(yara_rule.Yara_rule.state == state)
        ips = ips.filter(c2ip.C2ip.state == state)
        dns = dns.filter(c2dns.C2dns.state == state)
        task = task.filter(tasks.Tasks.state == state)

    if category:
        signatures = signatures.filter(yara_rule.Yara_rule.category == category)

    if all:
        signatures = signatures.filter(
            or_(yara_rule.Yara_rule.name.like("%" + all + "%"), yara_rule.Yara_rule.category.like("%" + all + "%"),
                yara_rule.Yara_rule.state.like("%" + all + "%"), yara_rule.Yara_rule.strings.like("%" + all + "%"),
                yara_rule.Yara_rule.condition.like("%" + all + "%"),
                yara_rule.Yara_rule.description.like("%" + all + "%"),
                yara_rule.Yara_rule.references.like("%" + all + "%"),
                (yara_rule.Yara_rule.eventid == int(all) if all.isdigit() else False)))

        ips = ips.filter(or_(c2ip.C2ip.state.like("%" + all + "%"),
                             c2ip.C2ip.ip.like("%" + all + "%"),
                             c2ip.C2ip.asn.like("%" + all + "%"),
                             c2ip.C2ip.country.like("%" + all + "%"),
                             c2ip.C2ip.description.like("%" + all + "%"),
                             c2ip.C2ip.references.like("%" + all + "%"),
                             c2ip.C2ip.state.like("%" + all + "%"), ))
        dns = dns.filter(or_(c2dns.C2dns.state.like("%" + all + "%"),
                             c2dns.C2dns.domain_name.like("%" + all + "%"),
                             c2dns.C2dns.description.like("%" + all + "%"),
                             c2dns.C2dns.references.like("%" + all + "%"),
                             ))
        task = task.filter(or_(tasks.Tasks.state.like("%" + all + "%"), tasks.Tasks.title.like("%" + all + "%"),
                               tasks.Tasks.final_artifact.like("%" + all + "%")))

    if not artifact_type or "signature" in artifact_type:
        results["signatures"] = [signature.to_dict() for signature in signatures.all()]

    if not artifact_type or "ip" in artifact_type:
        results["ips"] = [ip.to_dict() for ip in ips.all()]

    if not artifact_type or "dns" in artifact_type:
        results["dns"] = [d.to_dict() for d in dns.all()]

    if not artifact_type or "task" in artifact_type:
        results["tasks"] = [t.to_dict() for t in task.all()]

    return Response(json.dumps(results), mimetype='application/json')
