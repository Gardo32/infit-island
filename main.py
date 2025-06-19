from flask import Flask
from flask_socketio import SocketIO
from api import init_api_routes
from web.app import socketio, configure_web_routes

app = Flask(__name__)
socketio.init_app(app)  # Initialize socketio with our Flask app
init_api_routes(app)    # Register API routes
configure_web_routes(app)  # Register web routes

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
