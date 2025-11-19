import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the scopes you need
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_refresh_token():
    creds = None

    # Check if we have saved credentials
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    print("\n✅ Tokens obtinguts correctament!")
    print(f"\nAccess Token: {creds.token}")
    print(f"\nRefresh Token: {creds.refresh_token}")
    print(f"\nClient ID: {creds.client_id}")
    print(f"\nClient Secret: {creds.client_secret}")

    return creds


if __name__ == "__main__":
    get_refresh_token()
