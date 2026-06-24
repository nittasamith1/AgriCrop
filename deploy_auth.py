import google.auth
from google.oauth2 import service_account
import google.auth.transport.requests

# Path to the service account key
SERVICE_ACCOUNT_FILE = 'serviceAccountKey.json'

# Scopes needed for Firebase CLI deployment
SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/firebase'
]

def get_access_token():
    try:
        # Load credentials from the service account file
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        # Create a request to refresh/fetch the token
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        
        # Print only the token so we can capture it in bash/powershell
        print(credentials.token)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    get_access_token()
