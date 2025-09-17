import serverless_wsgi
from src.main import app  # Import your full Flask app

def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
