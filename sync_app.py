import time
from sync_google_tasks import get_tasks
from notion_integration import create_notion_page, update_notion_page, delete_notion_page
from synced_tasks import load_synced_tasks, save_synced_tasks

def sync_tasks():
    google_tasks = get_tasks()
    if not google_tasks:
        print("No tasks found in Google Tasks.")
        return
    
    # Load mapping: {google_task_id: {"notion_page_id": ..., "last_updated": ...}}
    synced_tasks = load_synced_tasks()
    # Convert list of tasks into a dict for quick lookup
    google_tasks_dict = {task["id"]: task for task in google_tasks if "id" in task}
    
    # Process new and updated tasks
    for google_id, task in google_tasks_dict.items():
        if google_id not in synced_tasks:
            # New task – create Notion page.
            notion_page_id = create_notion_page(task)
            if notion_page_id:
                synced_tasks[google_id] = {
                    "notion_page_id": notion_page_id,
                    "last_updated": task.get("updated")
                }
        else:
            # Existing task – check if updated.
            stored = synced_tasks[google_id]
            if task.get("updated") != stored.get("last_updated"):
                if update_notion_page(stored["notion_page_id"], task):
                    synced_tasks[google_id]["last_updated"] = task.get("updated")
    
    # Process deletions: if a task exists in synced_tasks but not in Google Tasks, archive its page.
    for google_id in list(synced_tasks.keys()):
        if google_id not in google_tasks_dict:
            notion_page_id = synced_tasks[google_id]["notion_page_id"]
            if delete_notion_page(notion_page_id):
                del synced_tasks[google_id]
    
    save_synced_tasks(synced_tasks)

if __name__ == '__main__':
    while True:
        print("Syncing tasks from Google Tasks to Notion...")
        sync_tasks()
        print("Sync complete. Waiting for 15 seconds before next check.\n")
        time.sleep(15)
