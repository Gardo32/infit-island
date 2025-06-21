"""
Logging configuration for the application.
This module configures logging for the entire application.
"""
import logging
import sys

class PyMongoMessageFilter(logging.Filter):
    """
    Filter to exclude specific debug messages from pymongo.
    """
    def filter(self, record):
        # Filter out pymongo heartbeat messages.
        # The record.msg for pymongo.topology can be a LogMessage object, not a string or dict.
        # To avoid a TypeError, we must handle it carefully.
        if record.name == 'pymongo.topology':
            # record.getMessage() safely gets the string representation.
            if 'Server heartbeat started' in record.getMessage():
                return False
        return True

def configure_logging(socket_handler=None):
    """
    Configure application logging with handlers for console and Socket.IO.
    - Console handler logs INFO and above.
    - Socket.IO handler logs DEBUG and above for the /logs page.
    """
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG)  # Capture everything at the root

    # Console Handler for CLI output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Log INFO and higher to console
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(PyMongoMessageFilter())
    root_logger.addHandler(console_handler)

    # Socket.IO Handler for /logs page
    if socket_handler:
        socket_handler.setLevel(logging.DEBUG)  # Capture DEBUG and higher for web UI
        # Formatter is set in web/app.py where the handler is defined
        socket_handler.addFilter(PyMongoMessageFilter())
        root_logger.addHandler(socket_handler)

    # Set levels for noisy loggers to INFO or WARNING
    logging.getLogger('pymongo.topology').setLevel(logging.INFO)
    logging.getLogger('engineio.server').setLevel(logging.WARNING)
    logging.getLogger('socketio.server').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
