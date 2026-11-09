import logging
import os

def setup_logger():
    """Sets up the VANTHRIS logging system."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("VANTHRIS")
    logger.setLevel(logging.INFO)

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(os.path.join(log_dir, 'vanthris.log'), encoding='utf-8')

    c_format = logging.Formatter('%(message)s')
    f_format = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    if not logger.handlers:
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger

log = setup_logger()
