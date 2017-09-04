from app import app
import traceback
import re


@app.errorhandler(500)
def handle_500(error):
    app.logger.error("500 error message '%s'" % (error))
    return str(error), 500


@app.errorhandler(Exception)
def handle_exception(exception):
    app.logger.exception(exception)

    return "%s" % (
    re.sub(r'\"[^\"]+\/([^\"]+)', r"\1", traceback.format_exc().replace("\n", "<BR>").replace(" ", "&nbsp;"))), 500


@app.route('/InquestKB/error', methods=["GET"])
def do_error():
    return "Generic 500 error", 500


@app.route("/InquestKB/exception", methods=["GET"])
def do_exception():
    raise Exception("Generic 500 exception")
