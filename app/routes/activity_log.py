from flask import request, json, Response

from app import app, db, auto
from flask_login import login_required, current_user

from app.models import activity_log
from app.models.users import KBUser


@app.route('/ThreatKB/activity_log', methods=['GET'])
@auto.doc()
@login_required
def get_all_activity_logs():
    """Return a list of all activity logs

    Pagination variables:
    page_number: page number to start on, default 0
    page_size: the size of each page, default None (don't paginate)
    sort_by: column to sort by, must exist on the ActivityLog model, default None
    sort_direction: the direction to sort by if sorting, default ASC
    searches: dictionary of column filters as {column1:filter1, column2:filter2}, columns must exist on ActivityLog model, default {}

    Return: list of task dictionaries"""
    searches = request.args.get('searches', '{}')
    page_number = request.args.get('page_number', False)
    page_size = request.args.get('page_size', False)
    sort_by = request.args.get('sort_by', False)
    sort_direction = request.args.get('sort_dir', 'ASC')

    searches = json.loads(searches)

    entities = activity_log.ActivityLog.query

    if not current_user.admin:
        entities = entities.filter_by(owner_user_id=current_user.id)

    for column, value in searches.items():
        if not value:
            continue

        if column == "user.email":
            entities = entities.join(KBUser, activity_log.ActivityLog.user_id == KBUser.id).filter(
                KBUser.email.like("%" + str(value) + "%"))
            continue

        try:
            column = getattr(activity_log.ActivityLog, column)
            entities = entities.filter(column.like("%" + str(value) + "%"))
        except:
            continue

    filtered_entities = entities
    total_count = entities.count()

    if sort_by:
        filtered_entities = filtered_entities.order_by("%s %s" % (sort_by, sort_direction))
    else:
        filtered_entities = filtered_entities.order_by("activity_date DESC")

    if page_size:
        filtered_entities = filtered_entities.limit(int(page_size))

    if page_number:
        filtered_entities = filtered_entities.offset(int(page_number) * int(page_size))

    filtered_entities = filtered_entities.all()

    response_dict = dict()
    response_dict['data'] = [entity.to_dict() for entity in filtered_entities]
    response_dict['total_count'] = total_count

    return Response(json.dumps(response_dict), mimetype='application/json')
