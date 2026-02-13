import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="MSP API Manager",
    page_icon="📦",
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
    </style>
""", unsafe_allow_html=True)

# API Configuration
BASE_URL = "https://cthgcqdyqplumqizjngx.supabase.co/functions/v1/msp-api"

class MSPAPIClient:
    """Client for MSP API operations"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-MSP-API-Key": api_key  # Updated header name
        }
    
    def _make_request(self, action, **kwargs):
        """Make a request to the MSP API with the given action"""
        try:
            payload = {"action": action, **kwargs}
            
            print(f"DEBUG: Action: {action}")
            print(f"DEBUG: Payload: {payload}")
            
            response = requests.post(
                BASE_URL,
                headers=self.headers,
                json=payload
            )
            
            print(f"DEBUG: Response Status: {response.status_code}")
            print(f"DEBUG: Response: {response.text[:500]}")
            
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Exception: {type(e).__name__}: {str(e)}")
            return None, str(e)
    
    def test_connection(self):
        """Test the API connection and key validity"""
        try:
            # Try to list enboxes as a connection test
            result, error = self._make_request("list-enboxes")
            
            return {
                "list-enboxes": {
                    "status": "success" if not error else "failed",
                    "data": result if not error else None,
                    "error": error
                }
            }, None
        except Exception as e:
            return None, str(e)
    
    def get_enboxes(self):
        """Fetch all Enboxes"""
        return self._make_request("list-enboxes")
    
    def create_enbox(self, email, password=None, display_name=None, create_via="direct"):
        """Create a new Enbox - either direct (with password) or invite (without password)"""
        if create_via == "direct":
            if not password:
                return None, "Password is required for direct creation"
            return self._make_request(
                "create-enbox",
                email=email,
                password=password,
                displayName=display_name
            )
        else:
            # For invite creation
            return self._make_request(
                "create-enbox-invite",
                email=email,
                displayName=display_name
            )
    
    def get_enbox(self, enbox_id):
        """Get specific Enbox details"""
        return self._make_request("get-enbox", managedEnboxId=enbox_id)
    
    def activate_enbox(self, enbox_id):
        """Activate an Enbox"""
        return self._make_request("activate-enbox", managedEnboxId=enbox_id)
    
    def deactivate_enbox(self, enbox_id):
        """Deactivate an Enbox"""
        return self._make_request("deactivate-enbox", managedEnboxId=enbox_id)
    
    def get_stats(self):
        """Get MSP dashboard statistics"""
        return self._make_request("get-stats")
    
    def get_usage(self):
        """Get API usage statistics"""
        return self._make_request("get-usage")

def init_session_state():
    """Initialize session state variables"""
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'enboxes_data' not in st.session_state:
        st.session_state.enboxes_data = None

def authenticate():
    """Handle API key authentication from Streamlit secrets only"""
    st.markdown('<div class="main-header">🔐 MSP API Manager</div>', unsafe_allow_html=True)
    
    # Get API key from secrets only
    try:
        api_key = st.secrets["msp_api_key"]
        
        st.info(f"API Key loaded: {api_key[:12]}..." if len(api_key) > 12 else "API Key loaded (short)")
        st.info(f"Base URL: {BASE_URL}")
        
        # Test the connection first
        st.markdown("### 🔍 Testing Connection...")
        
        client = MSPAPIClient(api_key)
        
        with st.expander("🔧 Debug: Connection Test Results", expanded=True):
            test_results, test_error = client.test_connection()
            
            if test_error:
                st.error(f"Connection test failed: {test_error}")
            else:
                st.json(test_results)
        
        # Try to authenticate with actual endpoint
        st.markdown("### 🔐 Authenticating...")
        data, error = client.get_enboxes()
        
        if error:
            st.markdown(f'<div class="error-box">❌ Authentication failed: {error}</div>', unsafe_allow_html=True)
            
            st.markdown("""
                <div class="info-box">
                <strong>Troubleshooting Steps:</strong><br><br>
                1. Verify the edge function is deployed at the URL above<br>
                2. Check if the API key is valid and active (should start with 'enbox_msp_')<br>
                3. Ensure the edge function name is correct: <code>msp-api</code><br>
                4. Check the debug information above for specific error details
                </div>
            """, unsafe_allow_html=True)
            
            # Provide example request
            st.markdown("### 📋 Example API Request")
            example_curl = f"""curl -X POST \\
  {BASE_URL} \\
  -H "Content-Type: application/json" \\
  -H "X-MSP-API-Key: {api_key[:20]}..." \\
  -d '{{"action": "list-enboxes"}}'"""
            st.code(example_curl, language="bash")
            
        else:
            st.session_state.api_key = api_key
            st.session_state.authenticated = True
            st.success("✅ Authentication successful!")
            st.rerun()
            
    except KeyError:
        st.markdown('<div class="error-box">❌ API key not found in Streamlit secrets</div>', unsafe_allow_html=True)
        st.markdown("""
            <div class="info-box">
            <strong>Setup Instructions:</strong><br><br>
            Add your MSP API key to Streamlit secrets:<br><br>
            1. Create <code>.streamlit/secrets.toml</code> file<br>
            2. Add: <code>msp_api_key = "msp_your_key_here"</code><br>
            3. Restart the application
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f'<div class="error-box">❌ Error loading secrets: {str(e)}</div>', unsafe_allow_html=True)

def display_enboxes_list(client):
    """Display list of all Enboxes"""
    st.markdown('<div class="section-header">📦 Enboxes</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.enboxes_data = None
    
    # Fetch enboxes
    if st.session_state.enboxes_data is None:
        with st.spinner("Loading Enboxes..."):
            data, error = client.get_enboxes()
            
            if error:
                st.markdown(f'<div class="error-box">❌ Error loading Enboxes: {error}</div>', unsafe_allow_html=True)
                return
            
            st.session_state.enboxes_data = data
    
    data = st.session_state.enboxes_data
    
    # Extract enboxes array from response - handle different possible formats
    if isinstance(data, dict):
        # Try different possible response structures
        enboxes = data.get('enboxes', data.get('managedEnboxes', data.get('data', [])))
        count = data.get('count', len(enboxes))
    else:
        enboxes = data if isinstance(data, list) else []
        count = len(enboxes)
    
    if not enboxes or len(enboxes) == 0:
        st.info("No Enboxes found. Create your first one below!")
        return
    
    # Display stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Enboxes", count)
    with col2:
        active_count = sum(1 for e in enboxes if e.get("is_active", True))
        st.metric("Active", active_count)
    with col3:
        inactive_count = count - active_count
        st.metric("Inactive", inactive_count)
    
    # Convert to DataFrame for better display
    df_data = []
    for enbox in enboxes:
        df_data.append({
            "ID": enbox.get("id", "N/A"),
            "Rsync ID": enbox.get("enbox_rsync_id", "N/A"),
            "Display Name": enbox.get("display_name", "N/A"),
            "Created Via": enbox.get("created_via", "N/A"),
            "Status": "🟢 Active" if enbox.get("is_active", True) else "🔴 Inactive",
            "Created At": enbox.get("created_at", "N/A")[:10] if enbox.get("created_at") else "N/A"
        })
    
    df = pd.DataFrame(df_data)
    
    # Search functionality
    search_term = st.text_input("🔍 Search Enboxes", placeholder="Search by ID, name, or rsync ID...")
    
    if search_term:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        df = df[mask]
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Detailed view
    with st.expander("📋 View Detailed JSON"):
        selected_id = st.selectbox(
            "Select Enbox to view details",
            options=[enbox.get("id") for enbox in enboxes],
            format_func=lambda x: f"{x} - {next((e.get('display_name', 'N/A') for e in enboxes if e.get('id') == x), 'N/A')}"
        )
        
        if selected_id:
            selected_enbox = next((e for e in enboxes if e.get("id") == selected_id), None)
            if selected_enbox:
                st.json(selected_enbox)

def create_enbox_form(client):
    """Form to create a new Enbox"""
    st.markdown('<div class="section-header">➕ Create New Enbox</div>', unsafe_allow_html=True)
    
    # Choose creation method
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
            email = st.text_input(
                "Email *",
                placeholder="customer@example.com",
                help="Customer's email address"
            )
            display_name = st.text_input(
                "Display Name",
                placeholder="Customer Name (optional)",
                help="Customer's display name"
            )
        
        with col2:
            if create_method == "direct":
                password = st.text_input(
                    "Password *",
                    type="password",
                    placeholder="Minimum 6 characters",
                    help="Secure password for the Enbox"
                )
                st.info("💡 Direct creation: User account is created immediately with the provided password.")
            else:
                password = None
                st.info("💡 Invite creation: An invite link will be generated. User sets their own password when accepting the invite.")
        
        submitted = st.form_submit_button("Create Enbox", type="primary", use_container_width=True)
        
        if submitted:
            if not email:
                st.markdown('<div class="error-box">❌ Email is required</div>', unsafe_allow_html=True)
            elif "@" not in email:
                st.markdown('<div class="error-box">❌ Please enter a valid email address</div>', unsafe_allow_html=True)
            elif create_method == "direct" and not password:
                st.markdown('<div class="error-box">❌ Password is required for direct creation</div>', unsafe_allow_html=True)
            elif create_method == "direct" and len(password) < 6:
                st.markdown('<div class="error-box">❌ Password must be at least 6 characters</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Creating Enbox..."):
                    result, error = client.create_enbox(
                        email=email,
                        password=password,
                        display_name=display_name if display_name else None,
                        create_via=create_method
                    )
                    
                    if error:
                        st.markdown(f'<div class="error-box">❌ Error creating Enbox: {error}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="success-box">✅ Enbox created successfully!</div>', unsafe_allow_html=True)
                        
                        # Show different info based on creation method
                        if create_method == "invite":
                            st.markdown("### 📧 Invite Details")
                            
                            # Try to get invite_path first (new format), fallback to invite_link
                            invite_path = result.get('invite_path', '')
                            invite_link = result.get('invite_link', '')
                            invite_token = result.get('invite_token', 'N/A')
                            expires_at = result.get('invite_expires_at', 'N/A')
                            
                            # If we have invite_path, use it directly
                            if invite_path:
                                display_path = invite_path
                            # If we have invite_link with lovable.app, extract just the path
                            elif invite_link and '/invite/' in invite_link:
                                display_path = '/invite/' + invite_link.split('/invite/')[-1]
                            # Fallback to constructing from token
                            else:
                                display_path = f'/invite/{invite_token}' if invite_token != 'N/A' else 'N/A'
                            
                            st.code(display_path, language=None)
                            st.caption(f"Invite Token: {invite_token}")
                            st.caption(f"Expires: {expires_at[:10] if expires_at != 'N/A' else 'N/A'}")
                            st.info("📋 Append this path to your frontend URL (e.g., https://your-app.com/invite/...) and send it to the user.")
                        
                        with st.expander("📋 Full Response"):
                            st.json(result)
                        
                        st.session_state.enboxes_data = None  # Clear cache to refresh list
                        st.balloons()

def display_statistics(client):
    """Display MSP statistics and usage"""
    st.markdown('<div class="section-header">📊 Statistics & Usage</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Stats", use_container_width=True):
            pass  # Will refresh on rerun
    
    # Fetch stats
    with st.spinner("Loading statistics..."):
        stats_data, stats_error = client.get_stats()
        usage_data, usage_error = client.get_usage()
    
    if stats_error:
        st.markdown(f'<div class="error-box">❌ Error loading stats: {stats_error}</div>', unsafe_allow_html=True)
    else:
        st.markdown("### 📦 Enbox Statistics")
        
        stats = stats_data.get('stats', {})
        rate_limit = stats_data.get('rate_limit', {})
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Enboxes", stats.get('total_enboxes', 0))
        with col2:
            st.metric("Active Enboxes", stats.get('active_enboxes', 0))
        with col3:
            st.metric("Inactive Enboxes", stats.get('inactive_enboxes', 0))
        with col4:
            st.metric("API Calls (24h)", stats.get('api_calls_24h', 0))
        
        # Rate limit info
        st.markdown("---")
        st.markdown("### ⚡ Rate Limit Status")
        
        col1, col2 = st.columns(2)
        with col1:
            remaining = rate_limit.get('remaining', 0)
            st.metric("Requests Remaining", remaining)
        with col2:
            reset_at = rate_limit.get('reset_at', 'N/A')
            if reset_at != 'N/A':
                reset_time = reset_at.split('T')[1][:8] if 'T' in reset_at else reset_at
                st.metric("Resets At", reset_time)
    
    if usage_error:
        st.markdown(f'<div class="error-box">❌ Error loading usage: {usage_error}</div>', unsafe_allow_html=True)
    else:
        st.markdown("---")
        st.markdown("### 📈 API Usage (Last 24 Hours)")
        
        usage_stats = usage_data.get('usage', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### By Action")
            by_action = usage_stats.get('by_action', {})
            if by_action:
                action_df = pd.DataFrame([
                    {"Action": k, "Count": v} for k, v in by_action.items()
                ]).sort_values('Count', ascending=False)
                st.dataframe(action_df, use_container_width=True, hide_index=True)
            else:
                st.info("No API calls in the last 24 hours")
        
        with col2:
            st.markdown("#### By Status Code")
            by_status = usage_stats.get('by_status', {})
            if by_status:
                status_df = pd.DataFrame([
                    {"Status Code": k, "Count": v} for k, v in by_status.items()
                ]).sort_values('Count', ascending=False)
                st.dataframe(status_df, use_container_width=True, hide_index=True)
            else:
                st.info("No API calls in the last 24 hours")
        
        # Total requests
        st.metric("Total Requests (24h)", usage_stats.get('total_requests_24h', 0))

def manage_enbox(client):
    """Manage individual Enbox"""
    st.markdown('<div class="section-header">⚙️ Manage Enbox</div>', unsafe_allow_html=True)
    
    # Get list of enboxes for selection
    data, error = client.get_enboxes()
    
    if error or not data:
        st.warning("No Enboxes available to manage. Create one first!")
        return
    
    enboxes = data.get('enboxes', []) if isinstance(data, dict) else data
    
    if not enboxes or len(enboxes) == 0:
        st.warning("No Enboxes available to manage. Create one first!")
        return
    
    selected_id = st.selectbox(
        "Select Enbox to manage",
        options=[enbox.get("id") for enbox in enboxes],
        format_func=lambda x: f"{next((e.get('display_name', 'N/A') for e in enboxes if e.get('id') == x), 'N/A')} ({x[:8]}...)"
    )
    
    if not selected_id:
        return
    
    # Get selected enbox details
    selected_enbox = next((e for e in enboxes if e.get("id") == selected_id), None)
    is_active = selected_enbox.get("is_active", True) if selected_enbox else True
    
    tab1, tab2 = st.tabs(["📄 View Details", "⚙️ Activate/Deactivate"])
    
    with tab1:
        st.markdown("### Enbox Information")
        
        if st.button("🔄 Refresh Details", type="primary"):
            with st.spinner("Loading details..."):
                result, error = client.get_enbox(selected_id)
                
                if error:
                    st.markdown(f'<div class="error-box">❌ Error: {error}</div>', unsafe_allow_html=True)
                else:
                    enbox_detail = result.get('enbox', result)
                    
                    # Display key information
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Enbox ID", enbox_detail.get("id", "N/A")[:16] + "...")
                        st.metric("Display Name", enbox_detail.get("display_name", "N/A"))
                        st.metric("Created Via", enbox_detail.get("created_via", "N/A"))
                    with col2:
                        st.metric("Rsync ID", enbox_detail.get("enbox_rsync_id", "N/A"))
                        status = "🟢 Active" if enbox_detail.get("is_active", True) else "🔴 Inactive"
                        st.metric("Status", status)
                        created = enbox_detail.get("created_at", "N/A")
                        st.metric("Created", created[:10] if created != "N/A" else "N/A")
                    
                    # Show invite info if exists
                    if enbox_detail.get("invite_token"):
                        st.markdown("---")
                        st.markdown("### 📧 Invite Information")
                        st.info(f"Invite Token: {enbox_detail.get('invite_token', 'N/A')}")
                        if enbox_detail.get("invite_expires_at"):
                            expires = enbox_detail.get("invite_expires_at", "")
                            st.caption(f"Expires: {expires[:10] if expires else 'N/A'}")
                    
                    st.markdown("---")
                    with st.expander("📋 Full JSON Response"):
                        st.json(enbox_detail)
    
    with tab2:
        st.markdown("### Status Management")
        
        # Show current status
        status_col1, status_col2 = st.columns([1, 2])
        with status_col1:
            current_status = "🟢 Active" if is_active else "🔴 Inactive"
            st.metric("Current Status", current_status)
        
        st.markdown("---")
        
        # Activation/Deactivation buttons
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Activate Enbox")
            st.info("Enable this Enbox to allow access and operations.")
            if st.button("✅ Activate", type="primary", disabled=is_active, use_container_width=True):
                with st.spinner("Activating..."):
                    result, error = client.activate_enbox(selected_id)
                    
                    if error:
                        st.markdown(f'<div class="error-box">❌ Error: {error}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="success-box">✅ Enbox activated successfully!</div>', unsafe_allow_html=True)
                        st.json(result)
                        st.session_state.enboxes_data = None
                        st.rerun()
        
        with col2:
            st.markdown("#### Deactivate Enbox")
            st.warning("Disable this Enbox to restrict access and operations.")
            if st.button("🔴 Deactivate", type="secondary", disabled=not is_active, use_container_width=True):
                confirm = st.checkbox("I confirm I want to deactivate this Enbox", key="deactivate_confirm")
                
                if confirm and st.button("Confirm Deactivation", type="primary"):
                    with st.spinner("Deactivating..."):
                        result, error = client.deactivate_enbox(selected_id)
                        
                        if error:
                            st.markdown(f'<div class="error-box">❌ Error: {error}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="success-box">✅ Enbox deactivated successfully!</div>', unsafe_allow_html=True)
                            st.json(result)
                            st.session_state.enboxes_data = None
                            st.rerun()

def main():
    """Main application"""
    init_session_state()
    
    # Authentication check
    if not st.session_state.authenticated:
        authenticate()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔑 API Connection")
        st.success("✅ Connected")
        
        if st.button("🔓 Disconnect", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.api_key = None
            st.session_state.enboxes_data = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📚 Navigation")
        page = st.radio(
            "Select Page",
            ["Dashboard", "Create Enbox", "Manage Enbox", "Statistics"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption("MSP API Manager v1.0")
        st.caption("Manage customer Enboxes programmatically")
    
    # Initialize API client
    client = MSPAPIClient(st.session_state.api_key)
    
    # Main content
    st.markdown('<div class="main-header">📦 MSP API Manager</div>', unsafe_allow_html=True)
    
    if page == "Dashboard":
        display_enboxes_list(client)
    elif page == "Create Enbox":
        create_enbox_form(client)
    elif page == "Manage Enbox":
        manage_enbox(client)
    elif page == "Statistics":
        display_statistics(client)

if __name__ == "__main__":
    main()
