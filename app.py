import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import anthropic
import pandas as pd
import json
import csv
import io
import base64
import os
import re

# ============================================================
# RINGOVER BOTS
# Book of Business Bot & Process Bot
# ============================================================

# --- Page Configuration ---
st.set_page_config(
    page_title="Ringover Bots",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Ringover Brand Colors ---
NAVY = "#001b39"
TEAL = "#27c9d6"
WHITE = "#ffffff"

# --- Styling (Ringover branding with Poppins font) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp, .stMarkdown, .stTextInput, .stButton {{
        font-family: 'Poppins', sans-serif !important;
    }}

    .stApp {{
        background-color: {NAVY};
        color: {WHITE};
    }}

    /* FIX: FORCE PASSWORD INSTRUCTION TO WHITE */
    div[data-baseweb="input"] + div, 
    div[data-testid="stMarkdownContainer"] small,
    .stTextInput small,
    .stTextInput label {{
        color: #FFFFFF !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: #00122a;
    }}
    [data-testid="stSidebar"] * {{
        color: {WHITE} !important;
    }}

    /* Text input */
    .stTextInput input {{
        background-color: #00122a;
        color: {WHITE} !important;
        border: 1px solid {TEAL};
        border-radius: 6px;
    }}

    /* Bot Page Headers - FORCE SIZE AND BOLDNESS */
    .main-header {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 3.2rem !important; 
        font-weight: 800 !important; 
        color: #ffffff !important;
        margin-bottom: 0.5rem !important;
        display: block !important;
    }}

    .sub-header {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 1.2rem !important; 
        font-weight: 400 !important;
        color: #b8d4e3 !important;
        margin-bottom: 2rem !important;
        display: block !important;
    }}

    /* Landing page styling */
    .landing-question {{
        font-family: 'Poppins', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        color: {WHITE};
        text-align: center;
        margin: 2rem 0 0.5rem 0;
    }}
    .landing-subtitle {{
        font-family: 'Poppins', sans-serif;
        font-size: 1.2rem;
        font-weight: 300;
        color: #b8d4e3;
        text-align: center;
        margin-bottom: 3rem;
    }}

    .status-connected {{ color: {TEAL}; font-weight: 600; }}
    .status-error {{ color: #ff6b6b; font-weight: 600; }}

    /* Hide default branding */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    [data-testid="stHeader"] {{ background-color: transparent; height: 0; }}
    
    /* Force sidebar controls to white */
    html body [data-testid="stHeader"] button *,
    html body [data-testid="collapsedControl"] *,
    html body [data-testid="stSidebarCollapseButton"] * {{
        fill: #ffffff !important;
        color: #ffffff !important;
        stroke: #ffffff !important;
    }}
</style>
""", unsafe_allow_html=True)


# --- Logo Helper ---
def get_logo_base64():
    logo_path = os.path.join(os.path.dirname(__file__), "ringover-logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return None

def show_logo(max_width_px=320):
    logo_b64 = get_logo_base64()
    if logo_b64:
        st.markdown(f'<div style="text-align: center; margin-top: 1.5rem; margin-bottom: 1rem;"><img src="data:image/png;base64,{logo_b64}" style="max-width: {max_width_px}px; width: 80%;" /></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align: center; margin-top: 1.5rem; margin-bottom: 1rem;"><span style="color: {TEAL}; font-family: Poppins; font-weight: 700; font-size: 2.5rem;">ringover</span></div>', unsafe_allow_html=True)

# --- Load Credentials ---
def load_credentials():
    try:
        config = {
            "anthropic_api_key": st.secrets["secrets"]["ANTHROPIC_API_KEY"],
            "google_sheet_id": st.secrets["secrets"].get("GOOGLE_SHEET_ID", ""),
            "google_sheet_gid": str(st.secrets["secrets"].get("GOOGLE_SHEET_GID", "")).strip(),
            "google_sheet_tab_name": st.secrets["secrets"].get("GOOGLE_SHEET_TAB_NAME", "").strip(),
            "uk_google_sheet_id": st.secrets["secrets"].get("UK_GOOGLE_SHEET_ID", ""),
            "uk_google_sheet_gid": str(st.secrets["secrets"].get("UK_GOOGLE_SHEET_GID", "")).strip(),
            "uk_google_sheet_tab_name": st.secrets["secrets"].get("UK_GOOGLE_SHEET_TAB_NAME", "").strip(),
            "google_drive_folder_id": st.secrets["secrets"].get("GOOGLE_DRIVE_FOLDER_ID", ""),
            "google_credentials": json.loads(st.secrets["secrets"]["GOOGLE_CREDENTIALS_JSON"]),
            "app_password": st.secrets["secrets"].get("APP_PASSWORD", ""),
        }
        return config
    except Exception as e:
        st.error(f"Credentials Error: {e}")
        st.stop()

# --- Password Protection ---
def check_password(expected_password):
    if not expected_password or st.session_state.get("authenticated", False):
        return True

    show_logo(max_width_px=260)
    st.markdown('<div class="landing-question" style="font-size:1.6rem; text-align:center;">Please enter the access password</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Password", type="password", key="password_input", label_visibility="collapsed", placeholder="Password")
        if password:
            if password == expected_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password.")
    return False

# --- Google Auth Helper ---
def get_google_creds(credentials_info):
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly", "https://www.googleapis.com/auth/drive.readonly"]
    return Credentials.from_service_account_info(credentials_info, scopes=scopes)

# --- Data Loading (BoB) ---
@st.cache_data(ttl=300)
def load_sheet_data(_credentials, sheet_id, sheet_gid="", sheet_tab_name=""):
    creds = get_google_creds(_credentials)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = None
    if sheet_gid:
        try:
            gid_int = int(sheet_gid)
            for ws in spreadsheet.worksheets():
                if ws.id == gid_int:
                    worksheet = ws
                    break
        except: pass
    if worksheet is None and sheet_tab_name:
        try: worksheet = spreadsheet.worksheet(sheet_tab_name)
        except: worksheet = None
    if worksheet is None: worksheet = spreadsheet.sheet1
    return worksheet.get_all_records(), worksheet.title, [w.title for w in spreadsheet.worksheets()]

def data_to_dataframe(data):
    if not data: return pd.DataFrame()
    df = pd.DataFrame(data)
    number_pattern = re.compile(r"^-?\$?\s*-?[\d,]+(\.\d+)?%?$")
    for col in df.columns:
        if df[col].dtype != object: continue
        non_blank = df[col].astype(str).str.strip()
        non_blank = non_blank[non_blank != ""]
        if len(non_blank) == 0: continue
        if non_blank.apply(lambda v: bool(number_pattern.match(str(v).strip()))).mean() > 0.7:
            cleaned = df[col].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False).str.replace("%", "", regex=False).str.strip().replace("", None)
            df[col] = pd.to_numeric(cleaned, errors="coerce")
    return df

def dataframe_to_schema(df):
    if df.empty: return "Empty DataFrame."
    lines = [f"Total rows: {len(df)}", "Columns:"]
    for col in df.columns:
        lines.append(f'- "{col}" | {df[col].dtype} | samples: {df[col].dropna().head(2).tolist()}')
    return "\n".join(lines)

# --- Pandas Query Tool ---
def run_pandas_query(df, expression):
    try:
        result = eval(expression, {"__builtins__": {}}, {"df": df, "pd": pd})
        if isinstance(result, (pd.DataFrame, pd.Series)):
            return json.dumps(result.head(50).to_dict(), default=str)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# --- Process Bot Logic ---
@st.cache_data(ttl=600)
def load_drive_documents(_credentials, folder_id):
    creds = get_google_creds(_credentials)
    service = build("drive", "v3", credentials=creds)
    documents = []
    def read_folder(fid):
        query = f"'{fid}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        for file in results.get("files", []):
            if file["mimeType"] == "application/vnd.google-apps.folder": read_folder(file["id"])
            elif file["mimeType"] == "application/vnd.google-apps.document":
                content = service.files().export(fileId=file["id"], mimeType="text/plain").execute().decode("utf-8")
                documents.append({"name": file["name"], "content": content})
    read_folder(folder_id)
    return documents

# --- AI Logic ---
def ask_claude(client, question, system_prompt, chat_history):
    messages = [{"role": m["role"], "content": m["content"]} for m in chat_history]
    messages.append({"role": "user", "content": question})
    return client.messages.create(model="claude-sonnet-4-20250514", max_tokens=2048, system=system_prompt, messages=messages).content[0].text

# ============================================================
# LANDING PAGE
# ============================================================
def show_landing_page():
    with st.sidebar:
        show_logo(max_width_px=180)
        st.markdown("---")
        st.info("Select a bot below.")

    show_logo(max_width_px=340)

    st.markdown('<div class="landing-question">Which bot do you need to talk to?</div>', unsafe_allow_html=True)
    st.markdown('<div class="landing-subtitle">Choose a bot below to get started.</div>', unsafe_allow_html=True)

    col_left, col_us, col_gap1, col_uk, col_gap2, col_process, col_right = st.columns([0.5, 3, 0.3, 3, 0.3, 3, 0.5])

    with col_us:
        if st.button("USA BoB Bot", key="goto_bob", use_container_width=True):
            st.session_state["view"] = "bob"
            st.rerun()
    with col_uk:
        if st.button("UK BoB Bot", key="goto_uk_bob", use_container_width=True):
            st.session_state["view"] = "uk_bob"
            st.rerun()
    with col_process:
        if st.button("Process Bot", key="goto_process", use_container_width=True):
            st.session_state["view"] = "process"
            st.rerun()

# ============================================================
# BOT VIEW
# ============================================================
def show_bot_view(bot_mode, config):
    region = "UK" if bot_mode == "uk_bob" else "USA"
    
    with st.sidebar:
        show_logo(max_width_px=180)
        if st.button("← Back to Home", use_container_width=True):
            st.session_state["view"] = "landing"
            st.rerun()
        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Dynamic Headers based on bot
    if bot_mode == "process":
        st.markdown('<div class="main-header">📋 Process Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask about Ringover procedures and guidelines.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="main-header">{region} Book of Business Bot</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sub-header">Ask me anything about the {region} accounts.</div>', unsafe_allow_html=True)

    # Chat UI Logic
    current_key = f"{bot_mode}_messages"
    if current_key not in st.session_state: st.session_state[current_key] = []
    
    for message in st.session_state[current_key]:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    if prompt := st.chat_input("Ask me a question..."):
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state[current_key].append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                st.markdown("*(Claude AI response would generate here)*")

# ============================================================
# MAIN APP
# ============================================================
def main():
    config = load_credentials()
    if not check_password(config["app_password"]): st.stop()

    if "view" not in st.session_state: st.session_state["view"] = "landing"
    
    view = st.session_state["view"]
    if view == "landing": show_landing_page()
    else: show_bot_view(view, config)

if __name__ == "__main__":
    main()
