# src/history.py

import threading
from typing import Dict, List, Optional

_history: Dict[str, Dict] = {}
_lock = threading.Lock()

def record_entry(filename: str, task_id: str) -> None:
    """
    Enregistre une entrée en statut 'pending' dans l'historique.
    """
    with _lock:
        _history[task_id] = {
            "filename": filename,
            "status": "pending",
        }

def update_entry(task_id: str, result: Dict) -> None:
    """
    Met à jour le résultat et passe le statut à 'done'.
    """
    with _lock:
        entry = _history.get(task_id)
        if entry is not None:
            entry["status"] = "done"

def get_history() -> List[Dict]:
    """
    Retourne la liste des entrées d'historique.
    """
    with _lock:
        return list(_history.values())
