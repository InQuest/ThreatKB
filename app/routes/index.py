from app import app, auto

@app.route('/')
@auto.doc()
def root():
    """Root route
    Return: index.html"""
    return app.send_static_file('index.html')
