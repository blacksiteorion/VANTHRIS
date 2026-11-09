import logging
import os
import re

# Matches [tag], [/tag], [bold red], [/], [dim italic], etc.
_RICH_TAG = re.compile(r"\[/?[^\[\]]*\]")


class _StripMarkupFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = _RICH_TAG.sub("", record.msg)
        # Clean up doubled spaces left behind
        record.msg = re.sub(r"  +", " ", record.msg) if isinstance(record.msg, str) else record.msg
        return True


def setup_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("VANTHRIS")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # important for re-imports

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(os.path.join(log_dir, "vanthris.log"), encoding="utf-8")

    c_format = logging.Formatter("%(message)s")
    f_format = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    c_handler.addFilter(_StripMarkupFilter())
    f_handler.addFilter(_StripMarkupFilter())

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    return logger


log = setup_logger()
