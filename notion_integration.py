import requests
import json

# Replace these with your actual Notion integration token and database ID.
NOTION_TOKEN = ''
DATABASE_ID = ''

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def create_notion_page(task):
    url = "https://api.notion.com/v1/pages"
    properties = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": task.get('title', 'No Title')
                    }
                }
            ]
        },
        "GoogleTaskID": {
            "rich_text": [
                {
                    "text": {
                        "content": task.get('id')
                    }
                }
            ]
        },
        "Completed": {
            "checkbox": task.get('status') == 'completed'
        }
    }
    
    # Add Due date if available
    if task.get('due'):
        properties["Due"] = {
            "date": {
                "start": task.get('due')
            }
        }
    else:
        properties["Due"] = {
            "date": None
        }
    
    # Add Notes if available
    if task.get('notes'):
        properties["Notes"] = {
            "rich_text": [
                {
                    "text": {
                        "content": task.get('notes')
                    }
                }
            ]
        }
    else:
        properties["Notes"] = {
            "rich_text": []
        }
    
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code not in [200, 201]:
        print("Error creating page in Notion:", response.text)
        return None
    else:
        result = response.json()
        print("Created Notion page for task:", task.get('title'))
        return result.get("id")

def update_notion_page(notion_page_id, task):
    url = f"https://api.notion.com/v1/pages/{notion_page_id}"
    properties = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": task.get('title', 'No Title')
                    }
                }
            ]
        },
        "Completed": {
            "checkbox": task.get('status') == 'completed'
        }
    }
    
    if task.get('due'):
        properties["Due"] = {
            "date": {
                "start": task.get('due')
            }
        }
    else:
        properties["Due"] = {
            "date": None
        }
    
    if task.get('notes'):
        properties["Notes"] = {
            "rich_text": [
                {
                    "text": {
                        "content": task.get('notes')
                    }
                }
            ]
        }
    else:
        properties["Notes"] = {
            "rich_text": []
        }
    
    data = {
        "properties": properties
    }
    
    response = requests.patch(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        print("Error updating Notion page:", response.text)
        return False
    else:
        print("Updated Notion page for task:", task.get('title'))
        return True

def delete_notion_page(notion_page_id):
    url = f"https://api.notion.com/v1/pages/{notion_page_id}"
    data = {
        "archived": True
    }
    response = requests.patch(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        print("Error archiving Notion page:", response.text)
        return False
    else:
        print("Archived Notion page id:", notion_page_id)
        return True
