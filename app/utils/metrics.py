import threading
import logging
import requests
from time import sleep
from queue import Queue
from typing import Any

class Whisperer:
    # Queues for thread-safe logging and metric sending
    log_queue: Queue = Queue()
    metric_queue: Queue = Queue()

    def __init__(self, parameters: dict[str, Any] = None):
        if parameters:
            if log_params := parameters.get("log"):
                self.logger.setLevel(log_params.get("level"))
                self.logger.setFormatter(logging.Formatter(log_params.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")))
                if url := log_params.get("url"):
                    self.logger.addHandler(logging.StreamHandler(url))
                    self.logger.addHandler(logging.StreamHandler())
                else:
                    self.logger.addHandler(logging.StreamHandler())
            if metric_params := parameters.get("metric"):
                self._metrics_url = metric_params.get("url")
        self.start_signals()

    def log_worker(self):
        while True:
            record = self.log_queue.get()
            print(record)
            if record is None:
                break
            self.logger.info(record) # need to replace this with actual logging logic
            self.log_queue.task_done()

    def metric_worker(self):
        while True:
            record = self.metric_queue.get()
            print(record)
            if record is None:
                break

            if not self._metrics_url:
                self.logger.debug("No metrics URL provided. Skipping metric sending.")
                self.metric_queue.task_done()
                continue

            for i in range(10):
                try:
                    requests.post(self._metrics_url, data=record).raise_for_status()
                except requests.exceptions.RequestException as e:
                    if i == 10:
                        self.logger.error(f"Max retries exceeded (10). Failed to send metric {record}")
                        break
                    self.logger.error(f"Retry {i}. Failed to send metric: {e}")
                    sleep(2)
                    continue
            self.metric_queue.task_done()

    def start_signals(self):
        # Start the log and metric worker threads
        log_thread = threading.Thread(target=self.log_worker, daemon=True)
        log_thread.start()

        metric_thread = threading.Thread(target=self.metric_worker, daemon=True)
        metric_thread.start()


