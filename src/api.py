# src/api.py
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from typing import List
from .tasks import process_file, get_results
from .history import record_entry

app = FastAPI(title="OCR Green Hub API")

@app.post("/upload/")
async def upload(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    task_ids = []
    for f in files:
        content = await f.read()
        tid = process_file.delay(f.filename, content)
        task_ids.append(tid.id)
        record_entry(f.filename, tid.id)
    return {"task_ids": task_ids}

@app.get("/results/{task_id}")
def results(task_id: str):
    return get_results(task_id)

@app.get("/history/")
def history():
    return record_entry.get_history()
