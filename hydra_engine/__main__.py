import logging
from hydra_engine._logging import global_logging_config

from app import app
import uvicorn

logger = logging.getLogger("common_logger")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", log_config=global_logging_config, port=8000)
