import schemathesis as st
import requests

@st.auth(refresh_interval=None).apply_to(path_regex="hotel-offers")
class AmadeusAuth:
    def get(self, case, ctx):
        response = requests.post(
            "https://test.api.amadeus.com/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "WApa8t7xQafqfTyrHppowJFOGgIiuE67",
                "client_secret": "8JMKtAlP9xApfWn5",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()["access_token"]   # /access_token

    def set(self, case, token, ctx):
        case.headers = case.headers or {}
        case.headers["Authorization"] = f"Bearer {token}"

@st.auth(refresh_interval=None).apply_to(path_regex="youtube")
class YouTubeAuth:
    def get(self, case, ctx):
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": "174585466737-d6mvluv4picmuccu3odnba6q3k4lun1u.apps.googleusercontent.com",
                "client_secret": "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",
                "refresh_token": "1//0eAT7oTkCUq6iCgYIARAAGA4SNwF-L9IrMHGZkKkqe3Gz8lmuVyT3FzeDoCpLmkhcVb_WjkI2tR863stWRTxch_eBgZRJmClyKSk",
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def set(self, case, token, ctx):
        case.headers = case.headers or {}
        case.headers["Authorization"] = f"Bearer {token}"

@st.auth(refresh_interval=None).apply_to(path_regex="location")
class DHLAuth:
    def get(self, case, ctx):
        response = requests.post(
            "http://localhost:8000/dhl",
            data={"name": "dhl"},   # x-www-form-urlencoded
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def set(self, case, token, ctx):
        case.headers = case.headers or {}
        case.headers["DHL-API-Key"] = token     # no prefix

@st.auth(refresh_interval=None).apply_to(path_regex="business")
class YelpAuth:
    def get(self, case, ctx):
        response = requests.post(
            "http://localhost:8000/yelp",
            data={"name": "yelp"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def set(self, case, token, ctx):
        case.headers = case.headers or {}
        case.headers["Authorization"] = f"Bearer {token}"



# @st.hook("before_call")
def handle_foursquare_header(context, case: st.Case, **kwargs):
    # Ensure headers dict exists (recommended pattern)
    if case.headers is None:
        case.headers = {}

    base_url = case.operation.base_url or ""

    if "foursquare.com" not in base_url:
        return
    case.headers["X-Places-Api-Version"] = "2025-06-17"  
    
