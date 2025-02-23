from __future__ import print_function
import os.path
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scope – here we need read access to your tasks.
SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']

def get_google_tasks_service():
    creds = None
    # token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, request the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run.
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('tasks', 'v1', credentials=creds)
    return service

def get_tasks(tasklist_id='@default'):
    service = get_google_tasks_service()
    results = service.tasks().list(
        tasklist=tasklist_id, 
        showCompleted=True, 
        showHidden=True
    ).execute()
    tasks = results.get('items', [])
    return tasks


if __name__ == '__main__':
    tasks = get_tasks()
    for task in tasks:
        print(task.get('title'))
