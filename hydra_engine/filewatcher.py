from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import app


class EventHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        app.parse_config_files()
        app.read_controls_file("files/controls.meta")

    def on_created(self, event):
        pass

    def on_deleted(self, event):
        pass

    def on_modified(self, event):
        pass

    def on_moved(self, event):
        pass


def start_monitoring_files():
    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, path='files', recursive=True)
    observer.start()
