import datetime
import os
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from hydra_engine import _app
from hydra_engine.parser import HydraParametersInfo, read_hydra_ignore
from hydra_engine.configs import config

last_trigger_time = time.time()
file_event = threading.Event()


class EventHandler(FileSystemEventHandler):
    def __init__(self, ignore_dirs, ignore_extension):
        self.ignore_dirs = ignore_dirs
        self.ignore_extension = ignore_extension
        self.event_lock = threading.Lock()

    def on_any_event(self, event):
        global last_trigger_time
        global file_event
        current_time = time.time()
        with self.event_lock:
            if (not event.is_directory and len([item for item in self.ignore_dirs if item in event.src_path]) == 0
                    and len([item for item in self.ignore_extension if item in event.src_path]) == 0
                    and event.src_path.find('~') == -1 and (current_time - last_trigger_time) > 1):
                _app.parse_config_files()
                _app.read_ui_file(config.filespath)
                _app.read_wizard_file(config.filespath)
                HydraParametersInfo().set_modify_time()
                last_trigger_time = current_time
                file_event.set()
                file_event.clear()


def start_monitoring_files():
    ignore_dirs, ignore_extension = read_hydra_ignore()
    event_handler = EventHandler(ignore_dirs, ignore_extension)
    observer = Observer()
    observer.schedule(event_handler, path=config.filespath, recursive=True)
    observer.start()
