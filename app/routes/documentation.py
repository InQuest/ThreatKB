from app import app, auto


@app.route('/ThreatKB/documentation', methods=["GET"])
def documentation():
    """Generate and return API documentation
    Return: API documentation HTML string"""
    return auto.html(template="autodoc_threatkb.html")
