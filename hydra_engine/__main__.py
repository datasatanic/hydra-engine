import logging
import threading

from hydra_engine._logging import global_logging_config
from hydra_engine import app_static, start_monitoring_files
import uvicorn

logger = logging.getLogger("common_logger")

if __name__ == "__main__":
    monitor_lock = threading.Lock()


    def start_monitoring_with_lock():
        with monitor_lock:
            start_monitoring_files()


    monitoring_thread = threading.Thread(target=start_monitoring_with_lock)
    monitoring_thread.start()
    uvicorn.run(app_static, host="127.0.0.1", log_config=global_logging_config, port=8080)
    monitoring_thread.join()
