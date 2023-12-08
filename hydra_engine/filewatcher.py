import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from hydra_engine._app import parse_config_files, read_controls_file


base_dir = os.path.dirname(os.path.abspath(__file__))
class EventHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        if not event.is_directory:
            parse_config_files()
            read_controls_file(os.path.join(base_dir, "files"))


def start_monitoring_files():
    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.join(base_dir, "files"), recursive=True)
    observer.start()
