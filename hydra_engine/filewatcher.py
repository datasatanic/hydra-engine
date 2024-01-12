import datetime
import os
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from hydra_engine import _app
from hydra_engine.parser import HydraParametersInfo

base_dir = os.path.dirname(os.path.abspath(__file__))
last_trigger_time = time.time()
file_event = threading.Event()


class EventHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        global last_trigger_time
        global file_event
        current_time = time.time()
        if not event.is_directory and event.src_path.find('~') == -1 and (current_time - last_trigger_time) > 1:
            _app.parse_config_files()
            _app.read_ui_file(os.path.join(base_dir, "files"))
            _app.read_wizard_file(os.path.join(base_dir, "files"))
            HydraParametersInfo().set_modify_time()
            last_trigger_time = current_time
            file_event.set()
            file_event.clear()


def start_monitoring_files():
    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.join(base_dir, "files"), recursive=True)
    observer.start()
