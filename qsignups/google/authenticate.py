import json, os

from qsignups.database import DbManager
from qsignups.database.orm import Region

# If this gets modified, then all authenticated data (pickle data) needs to get flushed
SCOPES = [
  'https://www.googleapis.com/auth/calendar'
 ]

GOOGLE_CREDENTIALS = {
  "installed": {
    "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
    "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
    "redirect_uris": [],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://accounts.google.com/o/oauth2/token"
  }
}

def __load_region_credentials(team_id):
  region: Region = DbManager.get_record(Region, team_id)
  if region.google_auth_data:
    try:

      from google.oauth2.credentials import Credentials
      return Credentials.from_authorized_user_info(region.google_auth_data)
    except Exception as ex:
      print(f"Unable to get google google.oauth2.credentials: {ex}")
      return None
  else:
    return None

def __get_refreshed_credentials(team_id):
  try:

    from google.auth.transport.requests import Request

    region_credentials = __load_region_credentials(team_id)
    if region_credentials and region_credentials.valid:
      return region_credentials

    if region_credentials and region_credentials.expired and region_credentials.refresh_token:
      region_credentials.refresh(Request())
      DbManager.update_record(Region, team_id, {
        Region.google_auth_data: json.loads(region_credentials.to_json())
      })
    return region_credentials
  except Exception as ex:
    print(f"Unable to get Google google.auth.transport.requests: {ex}")
    return None

def is_connected(team_id):
  region_credentials = __get_refreshed_credentials(team_id)
  return region_credentials and region_credentials.valid

def connect(team_id):
  region_credentials = __get_refreshed_credentials(team_id)
  if region_credentials and region_credentials.valid:
    return region_credentials
  else:
    try:

      from google_auth_oauthlib.flow import InstalledAppFlow
      flow = InstalledAppFlow.from_client_config(
        client_config = GOOGLE_CREDENTIALS,
        scopes = SCOPES)
      region_credentials = flow.run_local_server(port=0)
    except Exception as ex:
      print(f"Unable to get google_auth_oauthlib: {ex}")
      pass

  if region_credentials:
    DbManager.update_record(Region, team_id, {
      Region.google_auth_data: json.loads(region_credentials.to_json())
    })
    return region_credentials
  else:
    return None

def disconnect(team_id):
  DbManager.update_record(Region, team_id, {
    Region.google_auth_data: None
  })
  return True
