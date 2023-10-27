import threading
import time
import exceler
from queue import Queue
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from datetime import datetime, timedelta


class MyHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = datetime.now()

    def on_modified(self, event):
        if datetime.now() - self.last_modified < timedelta(seconds=1):
            return
        else:
            self.last_modified = datetime.now()
        print(f'Event type: {event.event_type}  path : {event.src_path}')
        print(event.is_directory) # This attribute is also available

class CifWatcher:
    def __init__(self, log_viewer):
        # Initialize watchdog
        self.event_handler = FileSystemEventHandler()

        # Events to handle
        self.event_handler.on_modified = self.on_modified
        self.event_handler.on_created = self.on_created

        # Exceptions and requests:
        self.exceptions = ""
        self.requests = ""

        # Excel spreadsheet
        self.xl = ""

        # Thread
        self.q = Queue()
        self.xl_thread = threading.Thread()

        # Log viewer
        self.echo = log_viewer

        # Date Time
        self.last_modified = datetime.now()


    def initiate(self, settings):
        # Watchdog thread
        self.wdog_stop_event = threading.Event()
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=settings.path, recursive=True)
        self.watch_thread = threading.Thread(target=self.wdog_thread)
        self.watch_thread.start()
        # Excel thread
        self.exceptions = settings.exceptions
        self.requests = settings.requests
        self.xl_thread = threading.Thread(target=self.workload, args=[settings])
        self.xl_thread.start()

    def on_created(self, event):
        if (event.src_path.endswith(".cif") and not any(exception in event.src_path for exception in self.exceptions) and
                all(request.lower() in event.src_path for request in self.requests)):
            self.q.put(event.src_path)

    def on_modified(self, event):
        if (event.src_path.endswith(".cif") and not any(exception in event.src_path for exception in self.exceptions) and
                all(request.lower() in event.src_path for request in self.requests)):
            self.q.put(event.src_path)

        if event.src_path.endswith(".sum"):
            self.q.put(event.src_path)
            # Put processing of sum file in queue
            pass

    def workload(self, settings):
        while True:
            work = self.q.get()
            print(work)
            try:
                exceler.update_table(self.xl, work, settings, self.echo)
            except:
                self.echo.append_log_message("Excel file is probably busy...", err=True)
            if work == "STOP":
                self.observer.stop()
                break
            self.q.task_done()

    def wdog_thread(self):
        self.observer.start()
        while not self.wdog_stop_event.is_set():
            time.sleep(1)
        self.observer.stop()


def main():
    root_folder = "D:\\Python_Projects\\Logbooker\\test_data"
    wdog = CifWatcher(log_viewer=None)
    wdog.initiate(path=root_folder, settings=None)


if __name__ == "__main__":
    main()
