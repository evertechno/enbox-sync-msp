import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Enbox Management Portal",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .email-item {
        padding: 1rem;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        background-color: #f8f9fa;
    }
    .email-item:hover {
        background-color: #e9ecef;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# API Configuration
MSP_API_URL = "https://cthgcqdyqplumqizjngx.supabase.co/functions/v1/msp-api"
USER_API_URL = "https://cthgcqdyqplumqizjngx.supabase.co/functions/v1/user-api"

class MSPAPIClient:
    """Client for MSP API operations"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-MSP-API-Key": api_key
        }
    
    def _make_request(self, action, **kwargs):
        """Make a request to the MSP API with the given action"""
        try:
            payload = {"action": action, **kwargs}
            response = requests.post(MSP_API_URL, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.RequestException as e:
            return None, str(e)
    
    def get_enboxes(self):
        return self._make_request("list-enboxes")
    
    def create_enbox(self, email, password=None, display_name=None, create_via="direct"):
        if create_via == "direct":
            if not password:
                return None, "Password is required for direct creation"
            return self._make_request("create-enbox", email=email, password=password, displayName=display_name)
        else:
            return self._make_request("create-enbox-invite", email=email, displayName=display_name)
    
    def get_enbox(self, enbox_id):
        return self._make_request("get-enbox", managedEnboxId=enbox_id)
    
    def activate_enbox(self, enbox_id):
        return self._make_request("activate-enbox", managedEnboxId=enbox_id)
    
    def deactivate_enbox(self, enbox_id):
        return self._make_request("deactivate-enbox", managedEnboxId=enbox_id)
    
    def get_stats(self):
        return self._make_request("get-stats")
    
    def get_usage(self):
        return self._make_request("get-usage")

class UserAPIClient:
    """Client for User API operations (Email management)"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-Enbox-API-Key": api_key
        }
    
    def _make_request(self, action, **kwargs):
        """Make a request to the User API with the given action"""
        try:
            payload = {"action": action, **kwargs}
            response = requests.post(USER_API_URL, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.RequestException as e:
            return None, str(e)
    
    def get_profile(self):
        return self._make_request("get-profile")
    
    def list_emails(self, folder="inbox", limit=50, offset=0):
        return self._make_request("list-emails", folder=folder, limit=limit, offset=offset)
    
    def get_email(self, email_id):
        return self._make_request("get-email", emailId=email_id)
    
    def send_email(self, to, subject, body_text="", body_html="", cc=None, bcc=None, priority="normal"):
        return self._make_request(
            "send-email",
            to=to,
            cc=cc or [],
            bcc=bcc or [],
            subject=subject,
            bodyText=body_text,
            bodyHtml=body_html,
            priority=priority
        )
    
    def mark_read(self, email_id):
        return self._make_request("mark-read", emailId=email_id)
    
    def mark_unread(self, email_id):
        return self._make_request("mark-unread", emailId=email_id)
    
    def star(self, email_id):
        return self._make_request("star", emailId=email_id)
    
    def unstar(self, email_id):
        return self._make_request("unstar", emailId=email_id)
    
    def archive(self, email_id):
        return self._make_request("archive", emailId=email_id)
    
    def trash(self, email_id):
        return self._make_request("trash", emailId=email_id)
    
    def restore(self, email_id):
        return self._make_request("restore", emailId=email_id)
    
    def delete_draft(self, email_id):
        return self._make_request("delete-draft", emailId=email_id)
    
    def list_labels(self):
        return self._make_request("list-labels")
    
    def resolve_enbox(self, enbox_id):
        return self._make_request("resolve-enbox", enboxId=enbox_id)

def init_session_state():
    """Initialize session state variables"""
    if 'msp_authenticated' not in st.session_state:
        st.session_state.msp_authenticated = False
    if 'user_authenticated' not in st.session_state:
        st.session_state.user_authenticated = False
    if 'msp_api_key' not in st.session_state:
        st.session_state.msp_api_key = None
    if 'user_api_key' not in st.session_state:
        st.session_state.user_api_key = None
    if 'enboxes_data' not in st.session_state:
        st.session_state.enboxes_data = None
    if 'current_mode' not in st.session_state:
        st.session_state.current_mode = "MSP"

def authenticate_msp():
    """Handle MSP API authentication"""
    try:
        api_key = st.secrets.get("msp_api_key")
        if not api_key:
            raise KeyError("msp_api_key not found")
        
        client = MSPAPIClient(api_key)
        data, error = client.get_enboxes()
        
        if error:
            st.error(f"❌ MSP Authentication failed: {error}")
            return False
        else:
            st.session_state.msp_api_key = api_key
            st.session_state.msp_authenticated = True
            return True
    except KeyError:
        st.error("❌ MSP API key not found in secrets. Add 'msp_api_key' to .streamlit/secrets.toml")
        return False

def authenticate_user():
    """Handle User API authentication"""
    try:
        api_key = st.secrets.get("user_api_key")
        if not api_key:
            raise KeyError("user_api_key not found")
        
        client = UserAPIClient(api_key)
        data, error = client.get_profile()
        
        if error:
            st.error(f"❌ User Authentication failed: {error}")
            return False
        else:
            st.session_state.user_api_key = api_key
            st.session_state.user_authenticated = True
            return True
    except KeyError:
        st.error("❌ User API key not found in secrets. Add 'user_api_key' to .streamlit/secrets.toml")
        return False

# MSP Functions (from previous code)
def display_enboxes_list(client):
    """Display list of all Enboxes"""
    st.markdown('<div class="section-header">📦 Enboxes</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.enboxes_data = None
    
    if st.session_state.enboxes_data is None:
        with st.spinner("Loading Enboxes..."):
            data, error = client.get_enboxes()
            if error:
                st.error(f"❌ Error loading Enboxes: {error}")
                return
            st.session_state.enboxes_data = data
    
    data = st.session_state.enboxes_data
    
    if isinstance(data, dict):
        enboxes = data.get('enboxes', data.get('managedEnboxes', data.get('data', [])))
        count = data.get('count', len(enboxes))
    else:
        enboxes = data if isinstance(data, list) else []
        count = len(enboxes)
    
    if not enboxes or len(enboxes) == 0:
        st.info("No Enboxes found. Create your first one below!")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Enboxes", count)
    with col2:
        active_count = sum(1 for e in enboxes if e.get("is_active", True))
        st.metric("Active", active_count)
    with col3:
        inactive_count = count - active_count
        st.metric("Inactive", inactive_count)
    
    df_data = []
    for enbox in enboxes:
        df_data.append({
            "ID": enbox.get("id", "N/A")[:8] + "...",
            "Rsync ID": enbox.get("enbox_rsync_id", "N/A"),
            "Display Name": enbox.get("display_name", "N/A"),
            "Created Via": enbox.get("created_via", "N/A"),
            "Status": "🟢 Active" if enbox.get("is_active", True) else "🔴 Inactive",
            "Created": enbox.get("created_at", "N/A")[:10] if enbox.get("created_at") else "N/A"
        })
    
    df = pd.DataFrame(df_data)
    search_term = st.text_input("🔍 Search Enboxes", placeholder="Search by ID, name, or rsync ID...")
    
    if search_term:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        df = df[mask]
    
    st.dataframe(df, use_container_width=True, hide_index=True)

def create_enbox_form(client):
    """Form to create a new Enbox"""
    st.markdown('<div class="section-header">➕ Create New Enbox</div>', unsafe_allow_html=True)
    
    create_method = st.radio(
        "Creation Method",
        options=["direct", "invite"],
        format_func=lambda x: "Direct (with password)" if x == "direct" else "Invite Link (user sets password)",
        horizontal=True
    )
    
    st.markdown("---")
    
    with st.form("create_enbox_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input("Email *", placeholder="customer@example.com")
            display_name = st.text_input("Display Name", placeholder="Customer Name (optional)")
        
        with col2:
            if create_method == "direct":
                password = st.text_input("Password *", type="password", placeholder="Minimum 6 characters")
                st.info("💡 Direct: Account created immediately")
            else:
                password = None
                st.info("💡 Invite: User sets password via link")
        
        submitted = st.form_submit_button("Create Enbox", type="primary", use_container_width=True)
        
        if submitted:
            if not email or "@" not in email:
                st.error("❌ Valid email required")
            elif create_method == "direct" and (not password or len(password) < 6):
                st.error("❌ Password must be at least 6 characters")
            else:
                with st.spinner("Creating Enbox..."):
                    result, error = client.create_enbox(email, password, display_name, create_method)
                    
                    if error:
                        st.error(f"❌ Error: {error}")
                    else:
                        st.success("✅ Enbox created successfully!")
                        
                        if create_method == "invite":
                            st.markdown("### 📧 Invite Details")
                            invite_path = result.get('invite_path', result.get('invite_link', ''))
                            if '/invite/' in invite_path:
                                invite_path = '/invite/' + invite_path.split('/invite/')[-1]
                            
                            st.code(invite_path, language=None)
                            st.caption(f"Token: {result.get('invite_token', 'N/A')}")
                            st.caption(f"Expires: {result.get('invite_expires_at', 'N/A')[:10]}")
                        
                        st.session_state.enboxes_data = None
                        st.balloons()

# Email Management Functions
def display_inbox(client):
    """Display inbox with email list"""
    st.markdown('<div class="section-header">📬 Inbox</div>', unsafe_allow_html=True)
    
    folder = st.selectbox("Folder", ["inbox", "sent", "drafts", "trash"])
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Emails", use_container_width=True):
            pass
    
    with st.spinner("Loading emails..."):
        data, error = client.list_emails(folder=folder, limit=50, offset=0)
    
    if error:
        st.error(f"❌ Error loading emails: {error}")
        return
    
    emails = data.get('emails', []) if isinstance(data, dict) else []
    
    if not emails:
        st.info(f"No emails in {folder}")
        return
    
    st.metric("Total Emails", len(emails))
    
    for email in emails:
        with st.expander(f"{'⭐' if email.get('is_starred') else '📧'} {email.get('subject', 'No Subject')} - {email.get('from_name', 'Unknown')}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.caption(f"From: {email.get('from_name', 'N/A')}")
                st.caption(f"Date: {email.get('created_at', 'N/A')[:10]}")
            
            with col2:
                if st.button("👁️ View Full", key=f"view_{email.get('id')}"):
                    view_email_detail(client, email.get('id'))
            
            with col3:
                email_actions(client, email)

def view_email_detail(client, email_id):
    """View full email details"""
    with st.spinner("Loading email..."):
        data, error = client.get_email(email_id)
    
    if error:
        st.error(f"❌ Error: {error}")
        return
    
    email = data.get('email', data) if isinstance(data, dict) else data
    
    st.markdown(f"### 📧 {email.get('subject', 'No Subject')}")
    st.markdown(f"**From:** {email.get('from_name', 'Unknown')} ({email.get('from_enbox_id', 'N/A')})")
    st.markdown(f"**Date:** {email.get('created_at', 'N/A')}")
    
    if email.get('bodyHtml'):
        st.markdown("**Body (HTML):**")
        st.markdown(email.get('bodyHtml'), unsafe_allow_html=True)
    elif email.get('bodyText'):
        st.markdown("**Body:**")
        st.text(email.get('bodyText'))
    
    if email.get('attachments'):
        st.markdown("**Attachments:**")
        for att in email.get('attachments', []):
            st.caption(f"📎 {att.get('filename', 'Unknown')}")

def email_actions(client, email):
    """Display email action buttons"""
    email_id = email.get('id')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if email.get('is_read'):
            if st.button("Mark Unread", key=f"unread_{email_id}"):
                client.mark_unread(email_id)
                st.rerun()
        else:
            if st.button("Mark Read", key=f"read_{email_id}"):
                client.mark_read(email_id)
                st.rerun()
    
    with col2:
        if email.get('is_starred'):
            if st.button("Unstar", key=f"unstar_{email_id}"):
                client.unstar(email_id)
                st.rerun()
        else:
            if st.button("Star", key=f"star_{email_id}"):
                client.star(email_id)
                st.rerun()
    
    with col3:
        if st.button("Archive", key=f"archive_{email_id}"):
            client.archive(email_id)
            st.success("Archived!")
            st.rerun()
    
    with col4:
        if st.button("Trash", key=f"trash_{email_id}"):
            client.trash(email_id)
            st.success("Moved to trash!")
            st.rerun()

def send_email_form(client):
    """Form to send a new email"""
    st.markdown('<div class="section-header">✉️ Send Email</div>', unsafe_allow_html=True)
    
    with st.form("send_email_form"):
        to = st.text_input("To (Enbox IDs, comma-separated)", placeholder="enbox_id1, enbox_id2")
        cc = st.text_input("CC (optional)", placeholder="enbox_id3")
        bcc = st.text_input("BCC (optional)", placeholder="enbox_id4")
        subject = st.text_input("Subject *")
        
        tab1, tab2 = st.tabs(["Plain Text", "HTML"])
        
        with tab1:
            body_text = st.text_area("Body (Plain Text)", height=200)
        
        with tab2:
            body_html = st.text_area("Body (HTML)", height=200)
        
        priority = st.selectbox("Priority", ["normal", "high", "low"])
        
        submitted = st.form_submit_button("Send Email", type="primary")
        
        if submitted:
            if not to or not subject:
                st.error("❌ 'To' and 'Subject' are required")
            else:
                to_list = [t.strip() for t in to.split(",")]
                cc_list = [c.strip() for c in cc.split(",")] if cc else []
                bcc_list = [b.strip() for b in bcc.split(",")] if bcc else []
                
                with st.spinner("Sending email..."):
                    result, error = client.send_email(
                        to=to_list,
                        subject=subject,
                        body_text=body_text,
                        body_html=body_html,
                        cc=cc_list,
                        bcc=bcc_list,
                        priority=priority
                    )
                
                if error:
                    st.error(f"❌ Error: {error}")
                else:
                    st.success("✅ Email sent successfully!")
                    st.balloons()

def user_profile_page(client):
    """Display user profile"""
    st.markdown('<div class="section-header">👤 Profile</div>', unsafe_allow_html=True)
    
    with st.spinner("Loading profile..."):
        data, error = client.get_profile()
    
    if error:
        st.error(f"❌ Error: {error}")
        return
    
    profile = data.get('profile', data) if isinstance(data, dict) else data
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Display Name", profile.get('display_name', 'N/A'))
        st.metric("Enbox ID", profile.get('enbox_id', 'N/A'))
    
    with col2:
        st.metric("Email", profile.get('email', 'N/A'))
        st.metric("Account Type", profile.get('account_type', 'N/A'))
    
    with st.expander("📋 Full Profile JSON"):
        st.json(profile)

def resolve_enbox_tool(client):
    """Tool to resolve Enbox IDs"""
    st.markdown('<div class="section-header">🔍 Resolve Enbox ID</div>', unsafe_allow_html=True)
    
    enbox_id = st.text_input("Enter Enbox ID to lookup")
    
    if st.button("Resolve", type="primary"):
        if not enbox_id:
            st.error("❌ Please enter an Enbox ID")
        else:
            with st.spinner("Resolving..."):
                data, error = client.resolve_enbox(enbox_id)
            
            if error:
                st.error(f"❌ Error: {error}")
            else:
                user = data.get('user', data) if isinstance(data, dict) else data
                st.success(f"✅ Found: {user.get('display_name', 'Unknown')}")
                st.json(user)

def main():
    """Main application"""
    init_session_state()
    
    st.markdown('<div class="main-header">📧 Enbox Management Portal</div>', unsafe_allow_html=True)
    
    # Mode selection
    mode = st.radio(
        "Select Mode",
        ["MSP (Manage Enboxes)", "User (Email Management)"],
        horizontal=True,
        key="mode_selector"
    )
    
    if "MSP" in mode:
        # MSP Mode
        if not st.session_state.msp_authenticated:
            if authenticate_msp():
                st.rerun()
            return
        
        client = MSPAPIClient(st.session_state.msp_api_key)
        
        with st.sidebar:
            st.success("✅ MSP Authenticated")
            if st.button("🔓 Disconnect MSP"):
                st.session_state.msp_authenticated = False
                st.session_state.msp_api_key = None
                st.rerun()
            
            st.markdown("---")
            page = st.radio("MSP Pages", ["Dashboard", "Create Enbox", "Statistics"])
        
        if page == "Dashboard":
            display_enboxes_list(client)
        elif page == "Create Enbox":
            create_enbox_form(client)
        elif page == "Statistics":
            st.markdown('<div class="section-header">📊 Statistics</div>', unsafe_allow_html=True)
            data, error = client.get_stats()
            if error:
                st.error(f"❌ Error: {error}")
            else:
                st.json(data)
    
    else:
        # User Mode
        if not st.session_state.user_authenticated:
            if authenticate_user():
                st.rerun()
            return
        
        client = UserAPIClient(st.session_state.user_api_key)
        
        with st.sidebar:
            st.success("✅ User Authenticated")
            if st.button("🔓 Disconnect User"):
                st.session_state.user_authenticated = False
                st.session_state.user_api_key = None
                st.rerun()
            
            st.markdown("---")
            page = st.radio("User Pages", ["Inbox", "Send Email", "Profile", "Resolve Enbox"])
        
        if page == "Inbox":
            display_inbox(client)
        elif page == "Send Email":
            send_email_form(client)
        elif page == "Profile":
            user_profile_page(client)
        elif page == "Resolve Enbox":
            resolve_enbox_tool(client)

if __name__ == "__main__":
    main()
