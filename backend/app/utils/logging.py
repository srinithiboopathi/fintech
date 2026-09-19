import logging
import re

API_KEY_REGEX = re.compile(r"(apikey=)[^&\s'\"]+", re.IGNORECASE)

class CredentialRedactingFilter(logging.Filter):
    """
    Ensures that any API keys embedded in log records (e.g. in URLs or debug messages)
    are automatically replaced with 'apikey=REDACTED'.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = API_KEY_REGEX.sub(r"\1REDACTED", record.msg)
        if record.args:
            args = []
            for arg in record.args:
                if isinstance(arg, str):
                    args.append(API_KEY_REGEX.sub(r"\1REDACTED", arg))
                else:
                    args.append(arg)
            record.args = tuple(args)
        return True

def setup_logger(name: str = "market_ingestion", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(CredentialRedactingFilter())
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()
