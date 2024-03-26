import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


class GoogleDriveHelper:

    def __init__(self, creds_path: str, token_path: str):

        self.creds = self.authenticate(creds_path, token_path)

    def authenticate(self, creds_path: str, token_path: str):
        
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = None

        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print("Error loading credentials:", e)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_path, "w") as token:
                token.write(creds.to_json())
            
        return creds


    def get_or_create_folder(self, folder_name):

        # Authenticate with Google Drive API
        drive_service = build("drive", "v3", credentials=self.creds)

        # Search for the folder by name
        response = drive_service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            fields="files(id)"
        ).execute()

        # If the folder exists, return its ID
        if "files" in response and len(response["files"]) > 0:
            return response['files'][0]['id']

        # Create folder metadata
        folder_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder"
        }

        # Create the folder
        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()

        return folder.get("id")


    def upload_csv_to_google_drive(self, file_path, folder_id=None):

        drive_service = build("drive", "v3", credentials=self.creds)

        file_metadata = {
            "name": os.path.basename(file_path),
            "mimeType": "text/csv"
        }
        if folder_id:
            file_metadata["parents"] = [folder_id]
           
        media = MediaFileUpload(file_path, mimetype="text/csv")

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True, 
            supportsTeamDrives=True
        ).execute()

        return file.get("id")

    


