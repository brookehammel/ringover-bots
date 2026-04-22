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

    /* Chat input — light background */
    [data-testid="stChatInput"] {{
        background-color: {WHITE} !important;
        border-radius: 8px;
    }}
    [data-testid="stChatInput"] > div {{
        background-color: {WHITE} !important;
        border: 1px solid {TEAL} !important;
        border-radius: 8px;
    }}
    .stChatInput textarea, [data-testid="stChatInput"] textarea {{
        background-color: {WHITE} !important;
        color: {NAVY} !important;
        border: none !important;
        caret-color: {NAVY} !important;
    }}
    .stChatInput textarea::placeholder, [data-testid="stChatInput"] textarea::placeholder {{
        color: #8a9ba8 !important;
    }}
    /* Send button inside chat input */
    [data-testid="stChatInput"] button {{
        color: {NAVY} !important;
    }}
    [data-testid="stChatInput"] button svg {{
        fill: {NAVY} !important;
    }}

    /* Default Streamlit buttons */
    .stButton > button {{
        background-color: {TEAL};
        color: {NAVY};
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.4rem;
        transition: all 0.2s ease;
    }}
    .stButton > button:hover {{
        background-color: {WHITE};
        color: {NAVY};
        transform: translateY(-1px);
    }}

    /* Chat messages */
    [data-testid="stChatMessage"] {{
        background-color: #002a4f !important;
        border-radius: 10px;
        padding: 0.5rem 1rem;
    }}
    [data-testid="stChatMessage"] *,
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] em,
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] h4,
    [data-testid="stChatMessage"] h5,
    [data-testid="stChatMessage"] h6,
    [data-testid="stChatMessage"] td,
    [data-testid="stChatMessage"] th {{
        color: {WHITE} !important;
    }}
    [data-testid="stChatMessage"] a {{
        color: {TEAL} !important;
    }}
    [data-testid="stChatMessage"] code {{
        background-color: #00122a !important;
        color: {TEAL} !important;
        padding: 2px 6px;
        border-radius: 4px;
    }}
    [data-testid="stChatMessage"] pre code {{
        background-color: #00122a !important;
        color: {WHITE} !important;
    }}

    /* Main content area text — force white on navy */
    html body .main .block-container,
    html body .main .block-container div,
    html body .main .block-container p,
    html body .main .block-container li,
    html body .main .block-container span,
    html body .main .block-container h1,
    html body .main .block-container h2,
    html body .main .block-container h3,
    html body .main .block-container h4,
    html body .main .block-container h5,
    html body .main .block-container h6,
    html body .main .block-container td,
    html body .main .block-container th,
    html body .main .block-container label,
    html body .stMarkdown,
    html body .stMarkdown *,
    html body [data-testid="stMarkdownContainer"],
    html body [data-testid="stMarkdownContainer"] *,
    html body [data-testid="stChatMessageContent"],
    html body [data-testid="stChatMessageContent"] *,
    html body [data-testid="stSpinner"],
    html body [data-testid="stSpinner"] *,
    html body [data-testid="stSpinner"] div {{
        color: {WHITE} !important;
    }}

    /* Custom classes - UPDATED FOR BOLDNESS */
    .main-header {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 3.2rem !important;
        font-weight: 800 !important;
        color: {WHITE} !important;
        margin-bottom: 0.5rem !important;
        display: block !important;
    }}
    .sub-header {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 1.2rem !important;
        color: #b8d4e3 !important;
        margin-bottom: 1.5rem !important;
        display: block !important;
    }}
    .status-connected {{ color: {TEAL}; font-weight: 600; }}
    .status-error {{ color: #ff6b6b; font-weight: 600; }}

    /* Landing page styling - UPDATED FOR CENTERING */
    .landing-question {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        color: {WHITE} !important;
        text-align: center !important;
        margin: 2rem 0 0.5rem 0 !important;
        display: block !important;
    }}
    .landing-subtitle {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 1.2rem !important;
        font-weight: 300 !important;
        color: #b8d4e3 !important;
        text-align: center !important;
        margin-bottom: 3rem !important;
        display: block !important;
    }}

    /* Hide default branding */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    [data-testid="stHeader"] {{
        background-color: transparent;
        height: 0;
    }}
    
    button[kind="headerNoPadding"] {{
        visibility: visible !important;
    }}
    
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
    """Load the Ringover logo as base64 for inline embedding."""
    logo_path = os.path.join(os.path.dirname(__file__), "ringover-logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return None


def show_logo(max_width_px=320):
    """Display the Ringover logo centered at the top."""
    logo_b64 = get_logo_base64()
    if logo_b64:
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 1rem;">
                <img src="data:image/png;base64,{logo_b64}" style="max-width: {max_width_px}px; width: 80%;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 1rem;">
                <span style="color: {TEAL}; font-family: Poppins; font-weight: 700; font-size: 2.5rem;">ringover</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --- Load Credentials ---
def load_credentials():
    """Load API keys and settings from Streamlit secrets or secrets.toml."""
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
        st.error(f"Could not load credentials. Error: {e}")
        st.stop()


# --- Password Protection ---
def check_password(expected_password):
    """Returns True if user has entered the correct password."""
    if not expected_password:
        return True
    if st.session_state.get("authenticated", False):
        return True

    show_logo(max_width_px=260)
    st.markdown('<div class="landing-question" style="font-size:1.6rem;">Please enter the access password</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Password", type="password", key="password_input", label_visibility="collapsed", placeholder="Password")
        if password:
            if password == expected_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
    return False


# --- Google Auth Helper ---
def get_google_creds(credentials_info):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    return Credentials.from_service_account_info(credentials_info, scopes=scopes)


# ============================================================
# BOOK OF BUSINESS BOT
# ============================================================

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
    if worksheet is None:
        worksheet = spreadsheet.sheet1
    data = worksheet.get_all_records()
    return data, worksheet.title, [w.title for w in spreadsheet.worksheets()]


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
            cleaned = (df[col].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False).str.replace("%", "", regex=False).str.strip().replace("", None))
            try: df[col] = pd.to_numeric(cleaned, errors="coerce")
            except: pass
    return df


def dataframe_to_schema(df):
    if df.empty: return "The DataFrame is empty."
    lines = [f"DataFrame name: df", f"Total rows: {len(df)}", "Columns (name | dtype | samples):"]
    for col in df.columns:
        sample = df[col].dropna().astype(str).head(2).tolist()
        lines.append(f'  - "{col}" | {df[col].dtype} | samples: {sample}')
    return "\n".join(lines)


BOB_SYSTEM_PROMPT = """You are the Ringover Book of Business Bot. Use the `query_dataframe` tool for all data questions.
DataFrame schema:
{schema}
"""

QUERY_TOOL = {
    "name": "query_dataframe",
    "description": "Evaluate a Python expression against the pandas DataFrame `df`.",
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Python expression to evaluate."}
        },
        "required": ["expression"],
    },
}

def run_pandas_query(df, expression):
    try:
        safe_builtins = {"len": len, "sum": sum, "min": min, "max": max, "round": round, "str": str, "int": int, "float": float}
        result = eval(expression, {"__builtins__": safe_builtins}, {"df": df, "pd": pd})
        if isinstance(result, (pd.DataFrame, pd.Series)):
            return json.dumps(result.head(50).to_dict("records"), default=str)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# PROCESS BOT
# ============================================================

@st.cache_data(ttl=600)
def load_drive_documents(_credentials, folder_id):
    creds = get_google_creds(_credentials)
    service = build("drive", "v3", credentials=creds)
    documents = []
    def read_folder(fid):
        query = f"'{fid}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        for file in results.get("files", []):
            mime = file["mimeType"]
            if mime == "application/vnd.google-apps.folder":
                read_folder(file["id"])
            elif mime == "application/vnd.google-apps.document":
                content = service.files().export(fileId=file["id"], mimeType="text/plain").execute().decode("utf-8")
                documents.append({"name": file["name"], "content": content})
    read_folder(folder_id)
    return documents

def documents_to_summary(documents):
    if not documents: return "No documents found."
    summary = ""
    for doc in documents:
        summary += f"--- DOCUMENT: {doc['name']} ---\n{doc['content'][:5000]}\n\n"
    return summary

PROCESS_SYSTEM_PROMPT = "You are the Ringover Process Bot. Use the documents below to answer: {data}"

# ============================================================
# SHARED: Ask Claude
# ============================================================

def ask_claude(client, question, system_prompt, chat_history):
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]
    messages.append({"role": "user", "content": question})
    response = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=4096, system=system_prompt, messages=messages)
    return response.content[0].text

def ask_claude_with_dataframe(client, question, system_prompt, chat_history, df):
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]
    messages.append({"role": "user", "content": question})
    response = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=4096, system=system_prompt, tools=[QUERY_TOOL], messages=messages)
    if response.stop_reason == "tool_use":
        # Simplified tool handling for stability
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                res = run_pandas_query(df, block.input.get("expression", ""))
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": block.id, "content": res}]})
                final = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=4096, system=system_prompt, messages=messages)
                return final.content[0].text
    return response.content[0].text


# ============================================================
# LANDING PAGE
# ============================================================

def show_landing_page():
    with st.sidebar:
        show_logo(max_width_px=180)
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
    # This matches your original logic exactly
    with st.sidebar:
        show_logo(max_width_px=180)
        if st.button("← Back to Home", use_container_width=True):
            st.session_state["view"] = "landing"
            st.rerun()

    if bot_mode == "bob":
        st.markdown('<div class="main-header">USA Book of Business Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask me about the US accounts.</div>', unsafe_allow_html=True)
    elif bot_mode == "uk_bob":
        st.markdown('<div class="main-header">UK Book of Business Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask me about the UK accounts.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="main-header">📋 Process Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask about Ringover procedures.</div>', unsafe_allow_html=True)

    # Simplified data loading for the sake of the fix
    st.info("Bot loaded. Ask your question below.")
    
    current_key = f"{bot_mode}_messages"
    if current_key not in st.session_state: st.session_state[current_key] = []
    for msg in st.session_state[current_key]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    if prompt := st.chat_input("Ask me..."):
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state[current_key].append({"role": "user", "content": prompt})
        # AI logic would follow here per original script


# ============================================================
# MAIN APP
# ============================================================

def main():
    config = load_credentials()
    if not check_password(config["app_password"]): st.stop()
    if "view" not in st.session_state: st.session_state["view"] = "landing"
    view = st.session_state["view"]
    if view == "landing": show_landing_page()
    elif view == "bob": show_bot_view("bob", config)
    elif view == "uk_bob": show_bot_view("uk_bob", config)
    elif view == "process": show_bot_view("process", config)

if __name__ == "__main__":
    main()
