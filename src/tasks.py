# src/tasks.py
from celery import Celery
from .celeryconfig import broker_url, result_backend
from .backends import TesseractBackend, TextractBackend
from .history import update_entry
from .nlp_postprocessing import normalize_entities

app = Celery('tasks', broker=broker_url, backend=result_backend)
app.config_from_object('celeryconfig')

@app.task
def process_file(filename: str, content: bytes):
    # Determine and convert formats
    # Choose backend based on arguments
    # Perform OCR, post-process, update history
    result = {"filename": filename, "entities": {}}
    update_entry(filename, result)
    return result

@app.task
def get_results(task_id: str):
    # Retrieve results for given task_id
    return {}
