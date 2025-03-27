import json

import requests

from chalicelib.setting import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


class GoogleOAuth2:
    def __init__(
        self,
        platform: str = "google",
        client_id: str = GOOGLE_CLIENT_ID,
        client_secret: str = GOOGLE_CLIENT_SECRET,
    ):
        self.platform = platform
        self.client_id = client_id
        self.client_secret = client_secret
        self.default_header = {"content-Type": "application/json"}

    def validate_auth_code(self, auth_code: str, redirect_uri: str):
        data = {
            "code": auth_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        response = requests.post(
            json=data,
            headers=self.default_header,
            url="https://accounts.google.com/o/oauth2/token",
            timeout=900
        )
        try:
            data_ = json.loads(response.text)
            return data_["access_token"], data_.get("refresh_token", None)
        except Exception:
            return None, None

    def _refresh_access_token(self, refresh_token: str):
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        response = requests.post(
            json=data,
            url="https://www.googleapis.com/oauth2/v4/token",
            headers=self.default_header,
            timeout=900
        )
        try:
            data = json.loads(response.text)
            return data["access_token"]
        except Exception:
            return None

    def get_user_info(self, access_token: str):
        response = requests.get(
            url=f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={access_token}",
            headers=self.default_header,
            timeout=900
        )
        try:
            data = json.loads(response.text)
            return {
                "email": data["email"],
                "user_id": data["sub"],
                "nickname": data["name"],
                "image": {"profile": data.get("picture", None)},
                "locale": data.get("locale", None)
            }
        except Exception:
            return {}

    def login(self, auth_code: str, access_token: str, refresh_token: str):
        new_refresh_token = None

        # if not access_token, new login
        if not access_token:
            (access_token, new_refresh_token) = self.validate_auth_code(auth_code)
            if not access_token:
                return "invalid auth code", {}
            if new_refresh_token:
                refresh_token = new_refresh_token

        new_data = self.get_user_info(access_token)

        # invalid access_token
        if not new_data:
            access_token = self._refresh_access_token(refresh_token)
            if not access_token:
                return "invalid refresh token", {}

            new_data = self.get_user_info(access_token)
            if not new_data:
                return "invalid access token", {}

        return "success", {
            **new_data,
            "access_token": access_token,
            "refresh_token": refresh_token
        }
        