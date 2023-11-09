import logging
import logging.handlers
import os
from datetime import datetime
import sys
#import openstack.utils

# Logging Levels
# https://docs.python.org/3/library/logging.html#logging-levels
# CRITICAL  50
# ERROR 40
# WARNING   30
# INFO  20
# DEBUG 10
# NOTSET    0


def set_up_logging(filPrefix="cqrun-"):
    file_path = sys.modules[__name__].__file__
    project_path = os.path.dirname(os.path.dirname(os.path.dirname(file_path)))
    log_location = project_path + '/logs/'
    if not os.path.exists(log_location):
        os.makedirs(log_location)

    current_time = datetime.now()
    current_date = current_time.strftime("%Y-%m")
    file_name = filPrefix + current_date + '.log'
    file_location = log_location + file_name
    with open(file_location, 'a+'):
        pass

    logger = logging.getLogger(__name__)
    fmt = '[%(asctime)s] [%(levelname)s] %(message)s @pid<%(process)d>'
    # To store in file
    # logging.basicConfig(format=fmt, filemode='a+', filename=file_location, level=logging.DEBUG)
    logging.basicConfig(format=fmt, filemode='a+', filename=file_location, level=logging.INFO)
    # To print only
    # logging.basicConfig(format=format, level=logging.DEBUG)
    return logger

