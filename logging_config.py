"""
Logging configuration for the application.
This module configures logging for the entire application.
"""
import logging

class PyMongoMessageFilter(logging.Filter):
    """
    Filter to exclude specific debug messages from pymongo.
    """
    def filter(self, record):
        # Filter out pymongo heartbeat messages
        if record.name == 'pymongo.topology' and 'message' in record.msg and 'Server heartbeat started' in record.msg:
            return False
        return True

def configure_logging():
    """
    Configure application logging with filters to suppress unwanted messages.
    """
    # Configure the root logger
    root_logger = logging.getLogger()
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create and configure a new handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add the filter to the handler
    pymongo_filter = PyMongoMessageFilter()
    handler.addFilter(pymongo_filter)
    
    # Add the handler to the root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    
    # Configure pymongo logger to use the filter directly as well
    pymongo_logger = logging.getLogger('pymongo.topology')
    pymongo_logger.addFilter(pymongo_filter)
    
    # This can be uncommented to completely silence pymongo.topology if needed
    # pymongo_logger.setLevel(logging.INFO)
