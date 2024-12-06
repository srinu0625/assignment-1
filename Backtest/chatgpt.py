import logging
import sys

# Create and configure the logger
logger = logging.getLogger('screenlog')
logger.setLevel(logging.DEBUG)

# Define the log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Terminal output handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# File output handler
file_handler = logging.FileHandler('screenlog.txt')
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Log some test messages
logger.debug('This is a debug message.')
logger.info('This is an info message.')
logger.warning('This is a warning message.')
logger.error('This is an error message.')
logger.critical('This is a critical message.')
