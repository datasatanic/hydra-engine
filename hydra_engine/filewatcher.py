from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from hydra_engine._app import parse_config_files, read_controls_file


class EventHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        if not event.is_directory:
            if "terragrunt-cache" not in event.src_path:
                print(event.src_path)
                parse_config_files()
                read_controls_file("files")


def start_monitoring_files():
    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, path='files', recursive=True)
    observer.start()
