import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from hydra_engine import _app
from hydra_engine.parser import HydraParametersInfo

base_dir = os.path.dirname(os.path.abspath(__file__))


class EventHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        if not event.is_directory:
            _app.parse_config_files()
            _app.read_ui_file(os.path.join(base_dir, "files"))
            _app.read_wizard_file(os.path.join(base_dir, "files"))
            HydraParametersInfo().set_modify_time()


def start_monitoring_files():
    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.join(base_dir, "files"), recursive=True)
    observer.start()
