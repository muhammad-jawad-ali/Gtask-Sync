#!/usr/bin/env python3
"""
Google Tasks to Notion Sync - Single File Version
=================================================

This script syncs your Google Tasks with a Notion database. It will:
  - Fetch tasks from your Google Tasks.
  - Create new pages in Notion for new tasks.
  - Update pages if tasks are modified.
  - Archive (delete) pages if tasks are removed from Google Tasks.

This single-file version includes all the functionality:
  - Google Tasks API integration.
  - Notion integration (including creating a new database if needed).
  - Local file management for tracking synced tasks.

===================================================================
Setup Instructions:
===================================================================

1. **Prerequisites:**
   - Install Python 3.6+.
   - Ensure you have a Google account and a Notion account.
   - Install the required packages. You can use:
     
         pip install google-auth google-auth-oauthlib google-api-python-client requests

2. **Google Tasks API Setup:**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or use an existing one.
   - Enable the **Google Tasks API** for your project.
   - Under **APIs & Services > Credentials**, create OAuth client ID credentials (choose “Desktop App”).
   - Download the `credentials.json` file and place it in the same folder as this script.

3. **Notion Integration Setup:**
   a. **Create a Notion Integration:**
      - Visit [Notion Integrations](https://www.notion.so/my-integrations) and click **New integration**.
      - Provide a name and select your workspace.
      - Copy your **Internal Integration Token**.
      - Paste it below in the `NOTION_TOKEN` variable.
   
   b. **Create a New Notion Database:**
      - This script can automatically create a new database for you.
      - The new database will have the following properties:
          - **Name:** Title property (type: title)
          - **Due:** Date property (type: date)
          - **Completed:** Checkbox property (type: checkbox)
          - **Notes:** Rich Text property (type: rich_text)
          - **GoogleTaskID:** Rich Text property (type: rich_text)
      - To create the database, you must set the `PARENT_PAGE_ID` variable (the ID of the Notion page under which the database will be created).
      - If you already have a database, set its ID in `DATABASE_ID` and skip the auto-creation.

   c. **Share the Database with Your Integration:**
      - In Notion, open your database page.
      - Click the three dots (•••) in the upper right corner.
      - Click **Share** and then **Add Connections**.
      - Search for your integration by name and invite it so it has access.

4. **Configuration:**
   - Set your Notion integration token in `NOTION_TOKEN`.
   - Set your Notion parent page ID in `PARENT_PAGE_ID`.
   - Optionally, set your existing Notion database ID in `DATABASE_ID` (if you want to use an existing database). Otherwise, leave it as None to auto-create one.

5. **Run the Script:**
   - Execute the script using:
     
         python sync_app.py

   The script will then sync your Google Tasks with your Notion database every 15 seconds.
===================================================================
"""

import os
import pickle
import json
import time
import requests

# ------------------ Google Tasks Integration ------------------ #
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scope for Google Tasks API (read-only)
SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']

def get_google_tasks_service():
    creds = None
    # token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for next time
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('tasks', 'v1', credentials=creds)
    return service

def get_tasks(tasklist_id='@default'):
    service = get_google_tasks_service()
    results = service.tasks().list(tasklist=tasklist_id, showCompleted=True).execute()
    tasks = results.get('items', [])
    return tasks

# ------------------ Notion Integration ------------------ #

# Set your Notion integration token here
NOTION_TOKEN = 'YOUR_NOTION_TOKEN_HERE'
# If you already have a database, set its ID here. Otherwise, leave as None to auto-create one.
DATABASE_ID = None
# Set the parent page ID under which the new database will be created.
PARENT_PAGE_ID = 'YOUR_PARENT_PAGE_ID_HERE'

notion_headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def create_notion_database():
    """
    Creates a new Notion database with the required schema.
    The database will include:
      - Name: Title property.
      - Due: Date property.
      - Completed: Checkbox property.
      - Notes: Rich Text property.
      - GoogleTaskID: Rich Text property.
    """
    url = "https://api.notion.com/v1/databases"
    data = {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE_ID},
        "title": [
            {
                "type": "text",
                "text": {"content": "Google Tasks Sync"}
            }
        ],
        "properties": {
            "Name": {"title": {}},
            "Due": {"date": {}},
            "Completed": {"checkbox": {}},
            "Notes": {"rich_text": {}},
            "GoogleTaskID": {"rich_text": {}}
        }
    }
    response = requests.post(url, headers=notion_headers, data=json.dumps(data))
    if response.status_code not in [200, 201]:
        print("Error creating Notion database:", response.text)
        return None
    result = response.json()
    new_db_id = result.get("id")
    print("Created new Notion database with id:", new_db_id)
    return new_db_id

def create_notion_page(task, database_id):
    """
    Creates a new Notion page in the specified database for the given task.
    """
    url = "https://api.notion.com/v1/pages"
    properties = {
        "Name": {
            "title": [
                {"text": {"content": task.get('title', 'No Title')}}
            ]
        },
        "GoogleTaskID": {
            "rich_text": [
                {"text": {"content": task.get('id', '')}}
            ]
        },
        "Completed": {
            "checkbox": task.get('status') == 'completed'
        }
    }
    
    # Add Due date if available
    if task.get('due'):
        properties["Due"] = {
            "date": {"start": task.get('due')}
        }
    else:
        properties["Due"] = {"date": None}
    
    # Add Notes if available
    if task.get('notes'):
        properties["Notes"] = {
            "rich_text": [
                {"text": {"content": task.get('notes')}}
            ]
        }
    else:
        properties["Notes"] = {"rich_text": []}
    
    data = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    
    response = requests.post(url, headers=notion_headers, data=json.dumps(data))
    if response.status_code not in [200, 201]:
        print("Error creating page in Notion:", response.text)
        return None
    result = response.json()
    print("Created Notion page for task:", task.get('title'))
    return result.get("id")

def update_notion_page(notion_page_id, task, database_id):
    """
    Updates an existing Notion page (specified by notion_page_id) with the latest task data.
    """
    url = f"https://api.notion.com/v1/pages/{notion_page_id}"
    properties = {
        "Name": {
            "title": [
                {"text": {"content": task.get('title', 'No Title')}}
            ]
        },
        "Completed": {
            "checkbox": task.get('status') == 'completed'
        }
    }
    
    if task.get('due'):
        properties["Due"] = {
            "date": {"start": task.get('due')}
        }
    else:
        properties["Due"] = {"date": None}
    
    if task.get('notes'):
        properties["Notes"] = {
            "rich_text": [
                {"text": {"content": task.get('notes')}}
            ]
        }
    else:
        properties["Notes"] = {"rich_text": []}
    
    data = {"properties": properties}
    response = requests.patch(url, headers=notion_headers, data=json.dumps(data))
    if response.status_code != 200:
        print("Error updating Notion page:", response.text)
        return False
    print("Updated Notion page for task:", task.get('title'))
    return True

def delete_notion_page(notion_page_id):
    """
    Archives the Notion page (simulating deletion) by setting it as archived.
    """
    url = f"https://api.notion.com/v1/pages/{notion_page_id}"
    data = {"archived": True}
    response = requests.patch(url, headers=notion_headers, data=json.dumps(data))
    if response.status_code != 200:
        print("Error archiving Notion page:", response.text)
        return False
    print("Archived Notion page with id:", notion_page_id)
    return True

# ------------------ Local Synced Tasks Management ------------------ #

def load_synced_tasks():
    """
    Loads the mapping of Google Task IDs to Notion page IDs and last updated timestamps.
    Stored in a local JSON file ("synced_tasks.json").
    """
    if os.path.exists("synced_tasks.json"):
        with open("synced_tasks.json", "r") as f:
            return json.load(f)
    return {}

def save_synced_tasks(task_mapping):
    """
    Saves the mapping of synced tasks to a JSON file.
    """
    with open("synced_tasks.json", "w") as f:
        json.dump(task_mapping, f)

# ------------------ Main Sync Logic ------------------ #

def sync_tasks(database_id):
    google_tasks = get_tasks()
    if not google_tasks:
        print("No tasks found in Google Tasks.")
        return
    
    # Load mapping: {google_task_id: {"notion_page_id": ..., "last_updated": ...}}
    synced_tasks = load_synced_tasks()
    # Convert list of tasks into a dict for quick lookup.
    google_tasks_dict = {task["id"]: task for task in google_tasks if "id" in task}
    
    # Process new and updated tasks
    for google_id, task in google_tasks_dict.items():
        if google_id not in synced_tasks:
            # Create new page in Notion
            notion_page_id = create_notion_page(task, database_id)
            if notion_page_id:
                synced_tasks[google_id] = {
                    "notion_page_id": notion_page_id,
                    "last_updated": task.get("updated")
                }
        else:
            # Check for updates
            stored = synced_tasks[google_id]
            if task.get("updated") != stored.get("last_updated"):
                if update_notion_page(stored["notion_page_id"], task, database_id):
                    synced_tasks[google_id]["last_updated"] = task.get("updated")
    
    # Process deletions: if a task exists in synced_tasks but not in Google Tasks, archive its page.
    for google_id in list(synced_tasks.keys()):
        if google_id not in google_tasks_dict:
            notion_page_id = synced_tasks[google_id]["notion_page_id"]
            if delete_notion_page(notion_page_id):
                del synced_tasks[google_id]
    
    save_synced_tasks(synced_tasks)

# ------------------ Main Execution ------------------ #

if __name__ == '__main__':
    # If DATABASE_ID is not set, attempt to create a new database.
    if not DATABASE_ID:
        DATABASE_ID = create_notion_database()
        if not DATABASE_ID:
            print("Failed to create a Notion database. Check your integration settings and PARENT_PAGE_ID.")
            exit(1)
        else:
            print("Remember to share the newly created database with your integration!")
            print("In Notion, click the three dots (•••) in the upper right, select 'Share', and add your integration under 'Add connections'.")
    
    print("Starting Google Tasks to Notion Sync...")
    while True:
        print("\nSyncing tasks...")
        sync_tasks(DATABASE_ID)
        print("Sync complete. Waiting 15 seconds before the next sync.\n")
        time.sleep(15)
