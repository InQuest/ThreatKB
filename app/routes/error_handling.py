from app import app, auto, db, current_user, request, Response
import traceback
import re
from app.models.errors import Error


@app.errorhandler(401)
def handle_401(err):
    return Response("", 401)


@app.errorhandler(409)
def handle_409(err):
    return str(err.description), 409


@app.errorhandler(500)
def handle_500(error):
    app.logger.error("500 error message '%s'" % (error))
    return str(error), 500


@app.errorhandler(Exception)
def handle_exception(exception):
    app.logger.exception(exception)
    db.session.rollback()

    stacktrace = "%s" % (
        re.sub(r'\"[^\"]+\/([^\"]+)', r"\1", traceback.format_exc().replace("\n", "<BR>").replace(" ", "&nbsp;")))

    err = Error(
        stacktrace=traceback.format_exc(),
        user_id=current_user.id,
        remote_addr=request.remote_addr,
        args=str(request.args.to_dict(flat=False)),
        method=request.method,
        route=request.url_rule
    )
    db.session.add(err)
    db.session.commit()

    stacktrace += str(exception.message)

    return stacktrace, exception.code if hasattr(exception, "code") else 500


@app.route('/ThreatKB/error', methods=["GET"])
@auto.doc()
def do_error():
    """Generate a fake HTTP 500 error"""
    return "Generic 500 error", 500


@app.route("/ThreatKB/exception", methods=["GET"])
@auto.doc()
def do_exception():
    """Generate a fake exception"""
    raise Exception("Generic 500 exception")
