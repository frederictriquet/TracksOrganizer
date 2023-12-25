import logging

logger = logging.getLogger('organizer')

# debug, info, warning, error, critical

def init_logger(level=logging.DEBUG):
    logging.basicConfig(
        level=level,
        # format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        format="%(levelname)s - %(module)s:%(lineno)d - %(message)s",
        force=True,
        handlers=[
            # logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )

def set_log_level(str_level: str):
    level = logging.getLevelName(str_level)
    init_logger(level)
