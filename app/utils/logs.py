import threading
import requests
import json
import logging
from logging import getLogger, getLevelName, StreamHandler, Formatter, Handler, DEBUG
from queue import Queue

from app.models import Parameters

# Global log handler
log_queue: Queue = Queue()

global_logger = getLogger("PyFlowAutomatorCore")
global_logger.setLevel(DEBUG)
global_logger.addHandler(StreamHandler())

def log_worker():
    while True:
        logger, log_type, record = log_queue.get()
        if record is None:
            break

        try:
            log_method = getattr(logger, log_type.lower(), None)
            if callable(log_method):
                log_method(record)
            else:
                logger.log(getattr(logging, log_type.upper(), DEBUG), record)
        except AttributeError:
            global_logger.error(f"Error in log_worker: AttributeError, log_type={log_type}")
        except Exception as e:
            global_logger.error(f"Error in log_worker: {str(e)}")

        log_queue.task_done()

log_thread = threading.Thread(target=log_worker, daemon=True)
log_thread.start()

class ProcessLogQueueHandler:
    loggers: dict[str, logging.Logger] = {}

    @classmethod
    def create_logger(cls, logger_name: str, parameters: Parameters):
        logger = getLogger(logger_name)
        logger.setLevel(DEBUG)
        logger.addHandler(StreamHandler())
        if parameters and parameters.log and parameters.log.url:
            handler = CustomHandler(parameters.log.url)
            handler.setLevel(getLevelName(parameters.log.level))
            if isinstance(parameters.log.format, str):
                formatter = Formatter(fmt=parameters.log.format)
            elif isinstance(parameters.log.format, dict):
                formatter = JSONFormatter(parameters.log.format)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        cls.loggers[logger_name] = logger
        return cls
    
    @classmethod
    def delete_logger(cls, logger_name: str):
        cls.loggers.pop(logger_name, None)

    @classmethod
    def log(cls, logger_name: str, log_type: str, record: str):
        logger = cls.loggers.get(logger_name)
        if logger:
            log_queue.put((logger, log_type, record))

class CustomHandler(Handler):
    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def emit(self, record):
        try:
            record = self.format(record)
            if isinstance(record, str):
                requests.post(self.url, data=record)
            elif isinstance(record, dict):
                requests.post(self.url, json=record)
        except (requests.exceptions.RequestException, Exception) as e:
            global_logger.error(f"Error in CustomHandler: {str(e)}")

class JSONFormatter(Formatter):
    def __init__(self, fmt: dict):
        super().__init__(json.dumps(fmt))

    def format(self, record) -> str:
        print(f"record: {record}")
        print(f"record.__dict__: {record.__dict__}")
        record.message = json.dumps(record.getMessage())[1:-1]
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        if record.exc_info and not record.exc_text:
            record.exc_text = json.dumps(self.formatException(record.exc_info))[1:-1]
        return self.formatMessage(record)