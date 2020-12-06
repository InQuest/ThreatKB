from flask import request, json, Response

from app import app, db, auto
from flask_login import login_required

from app.models import activity_log
from datetime import timedelta, datetime

from app.utilities import filter_entities


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
    sort_direction = request.args.get('sort_dir', 'DESC')
    try:
        since_days = int(request.args.get('since', 45))
    except:
        since_days = 45

    since = datetime.now() - timedelta(days=since_days)

    response_dict = filter_entities(entity=activity_log.ActivityLog,
                                    artifact_type="ACTIVITY_LOG",
                                    searches=searches,
                                    page_number=page_number,
                                    page_size=page_size,
                                    sort_by=sort_by,
                                    sort_direction=sort_direction,
                                    include_metadata=False,
                                    include_comments=False,
                                    exclude_totals=False,
                                    include_tags=False,
                                    default_sort="activity_date",
                                    include_merged=True,
                                    since=since)

    return Response(response_dict, mimetype='application/json')
