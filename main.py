from flask import Flask
from flask_socketio import SocketIO
from web.app import socketio, configure_web_routes, api_logger, llm_logger
from api import init_api_routes

# app.py now handles logging configuration

app = Flask(__name__)
socketio.init_app(app)  # Initialize socketio with our Flask app

# Pass the specific loggers to the API routes initialization
init_api_routes(app, api_logger, llm_logger)

configure_web_routes(app)  # Register web routes

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
