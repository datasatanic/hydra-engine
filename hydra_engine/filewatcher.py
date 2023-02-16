import queue
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import app
from watchdog.events import (
    EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_MOVED
)


class EventHandler(FileSystemEventHandler):
    def __init__(self, q):
        self._q = q
        super().__init__()

    def on_any_event(self, event):
        action = {
            EVENT_TYPE_CREATED: "Created",
            EVENT_TYPE_DELETED: "Deleted",
            EVENT_TYPE_MODIFIED: "Modified",
            EVENT_TYPE_MOVED: "Moved",
        }[event.event_type]
        if not event.is_directory:
            self._q.put((
                # Name of the modified file.
                Path(event.src_path).name,
                # Action executed on that file.
                action,
                app.parse_config_files(),
                app.read_controls_file("files/controls.meta"),
            ))


def start_monitoring_files():
    q = queue.Queue()
    event_handler = EventHandler(q)
    observer = Observer()
    observer.schedule(event_handler, path='files', recursive=True)
    observer.start()
