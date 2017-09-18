from app import app, auto
import traceback
import re


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

    return "%s" % (
    re.sub(r'\"[^\"]+\/([^\"]+)', r"\1", traceback.format_exc().replace("\n", "<BR>").replace(" ", "&nbsp;"))), 500


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
