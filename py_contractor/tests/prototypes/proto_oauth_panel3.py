# hmrc_panel_oauth.py
import panel as pn
import httpx
import secrets
import hashlib
import base64
import urllib.parse

# %% py_contractor imports
from py_contractor.config.config import Config

from py_contractor.config.loggers import PrototypeTestLogger

pn.extension()

# ---------------------------
# HMRC OAuth configuration
# ---------------------------
OAUTH_AUTHORIZE_URL = "https://test-www.tax.service.gov.uk/oauth/authorize"
OAUTH_TOKEN_URL = "https://test-api.service.hmrc.gov.uk/oauth/token"
CLIENT_ID = Config.hrmc_sandbox_client_id
SCOPE = "read:vat write:vat"
REDIRECT_URI = "http://localhost:5006"  # The Panel app URL

CLIENT_SECRET = "ebed6ff7-818c-4d47-8d22-db7544d58e16"

# ---------------------------
# Utility functions
# ---------------------------
def generate_pkce():
    """Generate PKCE code_verifier and code_challenge."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(40)).rstrip(b"=").decode()
    hashed = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(hashed).rstrip(b"=").decode()
    return verifier, challenge

def exchange_code_for_token(code, code_verifier):
    """Exchange authorization code for access token."""
    data = {
        "client_secret": CLIENT_SECRET,
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "code_verifier": code_verifier,
    }
    with httpx.Client() as client:
        resp = client.post(OAUTH_TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json().get("access_token")

# ---------------------------
# Dashboard UI
# ---------------------------
class HMRCDashboard(pn.viewable.Viewer):
    def __init__(self):
        # UI panes
        self.status = pn.pane.Markdown("### Not logged in.")
        self.login_button = pn.widgets.Button(name="Login with HMRC", button_type="primary")
        self.login_button.on_click(self.start_oauth)

        # Store PKCE verifier per session
        self.code_verifier = None
        self.state = None
        self.access_token = None
        
        # Hidden widgets to store state and code_verifier in the browser
        self.hidden_state = pn.widgets.StaticText()
        self.hidden_verifier = pn.widgets.StaticText()

        self.layout = pn.Column(
            "## HMRC OAuth PKCE Example",
            self.login_button,
            self.status,
        )

    # -------------------------------------------------------------------------
    def start_oauth(self, event):
        """Start OAuth flow by generating PKCE and redirect URL."""
        self.code_verifier, code_challenge = generate_pkce()
        self.state = secrets.token_urlsafe(16)
        
        # Store in hidden widgets (client-side)
        pn.state.cache["hidden_state"] = self.state
        pn.state.cache["hidden_verifier"] = self.code_verifier

        params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "scope": SCOPE,
            "state": self.state,
            "redirect_uri": REDIRECT_URI,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        url = f"{OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
        # Display clickable link for the user
        self.status.object = f"[Click here to authenticate with HMRC]({url})"

    # -------------------------------------------------------------------------
    def handle_redirect(self):
        """Check browser URL for OAuth redirect parameters and exchange code."""
        search = pn.state.location.search
        if not search:
            return
        
        params = urllib.parse.parse_qs(search[1:])  # remove ?
        code = params.get("code", [None])[0]
        returned_state = params.get("state", [None])[0]

        # Retrieve state/code_verifier from hidden widgets
        expected_state = pn.state.cache["hidden_state"]
        code_verifier = pn.state.cache["hidden_verifier"]
                
        # Already handled or no code
        if not code or self.access_token:
            return

        if returned_state != expected_state:
            self.status.object = "### State mismatch — possible CSRF!"
            return

        try:
            token = exchange_code_for_token(code, code_verifier)
            self.access_token = token
            self.status.object = "### Authentication complete! ✅"
        except Exception as e:
            self.status.object = f"### Error exchanging code: {e}"

    def view(self):
        # Periodically check the redirect URL in the browser
        pn.state.onload(lambda: self.handle_redirect())
        return self.layout


def run_dash():
    dash = HMRCDashboard()
    
    return dash.view()

# ---------------------------
# Serve the app
# ---------------------------
#dashboard = HMRCDashboard()
#pn.serve(dashboard.view, port=5006, threaded=True)
pn.serve(run_dash, port=5006, threaded=True)
