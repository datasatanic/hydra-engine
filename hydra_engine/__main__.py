import logging
from hydra_engine._logging import global_logging_config

from app import app
import uvicorn
from filewatcher import start_monitoring_files
logger = logging.getLogger("common_logger")


if __name__ == "__main__":
    start_monitoring_files()
    uvicorn.run(app, host="127.0.0.1", log_config=global_logging_config, port=8000)
