import time
import logging
from flask import request, g
from app import app

# Configure request logger
request_logger = logging.getLogger('threatkb.requests')
request_logger.setLevel(logging.INFO)

# Add file handler for request logging
request_handler = logging.FileHandler('/var/log/threatkb/requests.log')
request_handler.setLevel(logging.INFO)
request_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
))
request_logger.addHandler(request_handler)

@app.before_request
def before_request():
    """Log request start and store start time"""
    g.start_time = time.time()
    request_logger.info(f"REQUEST START: {request.method} {request.url} from {request.remote_addr}")
    if request.json:
        request_logger.info(f"REQUEST BODY: {request.json}")

@app.after_request
def after_request(response):
    """Log request completion with timing"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        request_logger.info(
            f"REQUEST END: {request.method} {request.url} -> "
            f"Status: {response.status_code} | "
            f"Duration: {duration:.3f}s | "
            f"Size: {response.content_length or 0} bytes"
        )
    return response

@app.errorhandler(Exception)
def log_exception(error):
    """Log all exceptions"""
    request_logger.error(
        f"EXCEPTION: {request.method} {request.url} -> "
        f"Error: {str(error)} | "
        f"Type: {type(error).__name__}"
    )
    # Re-raise the exception so normal error handling continues
    raise error
