#!/usr/bin/env python3
"""
Simple run script for the web application without TTS dependencies.
"""
import logging
import os
import sys
from flask import Flask
from flask_socketio import SocketIO

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import and configure logging
from logging_config import configure_logging
configure_logging()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Import the web configuration
from web.app import configure_web_routes, socketio

# Configure routes
configure_web_routes(app)

# Initialize SocketIO with the app
socketio.init_app(app, cors_allowed_origins="*")

if __name__ == '__main__':
    # Test some log messages with JSON
    logger = logging.getLogger(__name__)
    logger.info("Starting web application...")
    logger.debug('{"message": "Test debug message with JSON", "type": "test", "data": "sample"}')
    logger.debug('{"message": "LLM response received", "model": "gemma3:4b", "length": 150}')
    logger.info("Test regular info message without JSON")
    
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')
