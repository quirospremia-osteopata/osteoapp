from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def mostra_calendaris():
    creds = Credentials.from_authorized_user_file('token.json')
    service = build('calendar', 'v3', credentials=creds)

    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list['items']:
        print(f"📅 {cal['summary']} → ID: {cal['id']}")

if __name__ == '__main__':
    mostra_calendaris()
