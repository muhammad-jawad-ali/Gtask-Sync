import json
import os

def load_synced_tasks():
    if os.path.exists("synced_tasks.json"):
        with open("synced_tasks.json", "r") as f:
            return json.load(f)
    return {}


def save_synced_tasks(task_mapping):
    with open("synced_tasks.json", "w") as f:
        json.dump(task_mapping, f)
