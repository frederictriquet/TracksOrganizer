import logging

logger = logging.getLogger('organizer')

# debug, info, warning, error, critical

def init_logger(level=logging.DEBUG):
    logging.basicConfig(
        level=level,
        # format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        format="%(levelname)s - %(module)s:%(lineno)d - %(message)s",
        handlers=[
            # logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )
