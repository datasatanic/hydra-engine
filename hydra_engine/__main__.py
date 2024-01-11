import logging
import threading

from hydra_engine._logging import global_logging_config
from hydra_engine import app_static
import uvicorn

logger = logging.getLogger("common_logger")

if __name__ == "__main__":
    uvicorn.run(app_static, host="127.0.0.1", log_config=global_logging_config, port=8080)
