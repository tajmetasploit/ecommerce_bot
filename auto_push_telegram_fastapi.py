"""import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GitAutoPushHandler(FileSystemEventHandler):
    def __init__(self, debounce_seconds=5):
        self.last_push_time = 0
        self.debounce_seconds = debounce_seconds

    def on_any_event(self, event):
        # Ignore directory events and unwanted folders/files
        if event.is_directory or any(x in event.src_path for x in ['__pycache__', '.git', '.venv', 'env']):
            return
        
        current_time = time.time()
        if current_time - self.last_push_time < self.debounce_seconds:
            return
        
        self.last_push_time = current_time
        print(f"Detected change in {event.src_path}. Running git push...")

        try:
            # Stage all changes
            subprocess.run(["git", "add", "."], check=True)
            # Commit changes (if any)
            subprocess.run(["git", "commit", "-m", "Auto commit: updated Telegram FastAPI bot"], check=True)
            # Push to main branch
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("Pushed changes to GitHub successfully.")
        except subprocess.CalledProcessError as e:
            # This error usually happens if no changes to commit, so just ignore
            print(f"Git command failed or no changes to commit: {e}")

if __name__ == "__main__":

    path_to_watch = "."  # watch current directory, change if needed
    event_handler = GitAutoPushHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=True)
    observer.start()
    print(f"Watching '{path_to_watch}' for file changes to auto-push Telegram FastAPI bot updates...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Stopped watching.")

    observer.join()"""

import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GitAutoPushHandler(FileSystemEventHandler):
    def __init__(self, debounce_seconds=5):
        self.last_push_time = 0
        self.debounce_seconds = debounce_seconds

    def on_any_event(self, event):
        # Ignore directory events and unwanted folders/files
        if event.is_directory or any(x in event.src_path for x in ['__pycache__', '.git', '.venv', 'env']):
            return
        
        current_time = time.time()
        if current_time - self.last_push_time < self.debounce_seconds:
            return
        
        self.last_push_time = current_time
        print(f"Detected change in {event.src_path}. Running git push...")

        try:
            # Stage all changes
            subprocess.run(["git", "add", "."], check=True)
            # Commit changes (if any)
            subprocess.run(["git", "commit", "-m", "Auto commit: updated Telegram FastAPI bot"], check=True)
            # Pull latest changes from remote with rebase to avoid conflicts
            subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
            # Push to main branch
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("Pushed changes to GitHub successfully.")
        except subprocess.CalledProcessError as e:
            # This error usually happens if no changes to commit or conflicts during rebase, so just ignore
            print(f"Git command failed or no changes to commit: {e}")

if __name__ == "__main__":

    path_to_watch = "."  # watch current directory, change if needed
    event_handler = GitAutoPushHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=True)
    observer.start()
    print(f"Watching '{path_to_watch}' for file changes to auto-push Telegram FastAPI bot updates...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Stopped watching.")

    observer.join()
