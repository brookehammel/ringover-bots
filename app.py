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
        color: {WHITE};
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

    /* Main content area text — force white on navy (aggressive overrides) */
    html body .main .block-container,
    html body .main .block-container div,
    html body .main .block-container p,
    html body .main .block-container li,
    html body .main .block-container span,
    html body .main .block-container strong,
    html body .main .block-container em,
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
    html body .main .block-container a,
    html body .stMarkdown a {{
        color: {TEAL} !important;
    }}

    /* Keep button text in its intended color (overrides above) */
    html body .stButton > button,
    html body .stButton > button * {{
        color: {NAVY} !important;
    }}
    html body .stButton > button:hover,
    html body .stButton > button:hover * {{
        color: {NAVY} !important;
    }}

    /* Keep chat input text navy on its white background */
    html body [data-testid="stChatInput"] textarea,
    html body .stChatInput textarea {{
        color: {NAVY} !important;
    }}

    /* Custom classes */
    .main-header {{
        font-family: 'Poppins', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: {WHITE};
        margin-bottom: 0.25rem;
    }}
    .sub-header {{
        font-family: 'Poppins', sans-serif;
        font-size: 1rem;
        color: #b8d4e3;
        margin-bottom: 1.5rem;
    }}
    .status-connected {{ color: {TEAL}; font-weight: 600; }}
    .status-error {{ color: #ff6b6b; font-weight: 600; }}

    /* Landing page styling */
    .landing-question {{
        font-family: 'Poppins', sans-serif;
        font-size: 2.2rem;
        font-weight: 600;
        color: {WHITE};
        text-align: center;
        margin: 2rem 0 2.5rem 0;
    }}
    .landing-subtitle {{
        font-family: 'Poppins', sans-serif;
        font-size: 1.05rem;
        font-weight: 300;
        color: #b8d4e3;
        text-align: center;
        margin-bottom: 3rem;
    }}

    /* Big landing buttons */
    .big-bot-button {{
        display: block;
        width: 100%;
        background-color: {TEAL};
        color: {NAVY} !important;
        font-family: 'Poppins', sans-serif;
        font-size: 1.4rem;
        font-weight: 600;
        text-align: center;
        padding: 2.5rem 1rem;
        border-radius: 14px;
        text-decoration: none !important;
        transition: all 0.25s ease;
        border: 2px solid {TEAL};
    }}
    .big-bot-button:hover {{
        background-color: {NAVY};
        color: {TEAL} !important;
        border: 2px solid {TEAL};
        transform: translateY(-3px);
    }}
    .big-bot-emoji {{
        font-size: 2.5rem;
        display: block;
        margin-bottom: 0.5rem;
    }}
    .big-bot-caption {{
        font-size: 0.9rem;
        font-weight: 400;
        margin-top: 0.5rem;
        opacity: 0.85;
    }}

    /* Hide the default Streamlit header/footer branding but keep sidebar toggle */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    [data-testid="stHeader"] {{
        background-color: transparent;
        height: 0;
    }}
    
    /* Always keep the sidebar toggle button visible */
    [data-testid="stSidebar"][aria-expanded="false"] {{
        min-width: 0 !important;
    }}
    
    button[kind="headerNoPadding"] {{
        visibility: visible !important;
    }}
    
   /* The Nuclear Option: Force ALL icons in the header and sidebar controls to be white */
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
        # Fallback text if logo file not found
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
            # US Book of Business
            "google_sheet_id": st.secrets["secrets"].get("GOOGLE_SHEET_ID", ""),
            "google_sheet_gid": str(st.secrets["secrets"].get("GOOGLE_SHEET_GID", "")).strip(),
            "google_sheet_tab_name": st.secrets["secrets"].get("GOOGLE_SHEET_TAB_NAME", "").strip(),
            # UK Book of Business
            "uk_google_sheet_id": st.secrets["secrets"].get("UK_GOOGLE_SHEET_ID", ""),
            "uk_google_sheet_gid": str(st.secrets["secrets"].get("UK_GOOGLE_SHEET_GID", "")).strip(),
            "uk_google_sheet_tab_name": st.secrets["secrets"].get("UK_GOOGLE_SHEET_TAB_NAME", "").strip(),
            # Shared
            "google_drive_folder_id": st.secrets["secrets"].get("GOOGLE_DRIVE_FOLDER_ID", ""),
            "google_credentials": json.loads(st.secrets["secrets"]["GOOGLE_CREDENTIALS_JSON"]),
            "app_password": st.secrets["secrets"].get("APP_PASSWORD", ""),
        }
        return config
    except Exception as e:
        st.error(f"Could not load credentials. Make sure your secrets are set up correctly. Error: {e}")
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
    """
    Loads rows from a specific tab of the Google Sheet.
    """
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
        except (ValueError, TypeError):
            pass

    if worksheet is None and sheet_tab_name:
        try:
            worksheet = spreadsheet.worksheet(sheet_tab_name)
        except Exception:
            worksheet = None

    if worksheet is None:
        worksheet = spreadsheet.sheet1

    data = worksheet.get_all_records()
    return data, worksheet.title, [w.title for w in spreadsheet.worksheets()]


def data_to_dataframe(data):
    """Convert the sheet rows into a pandas DataFrame with numeric columns normalized."""
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    number_pattern = re.compile(r"^-?\$?\s*-?[\d,]+(\.\d+)?%?$")
    for col in df.columns:
        if df[col].dtype != object:
            continue
        non_blank = df[col].astype(str).str.strip()
        non_blank = non_blank[non_blank != ""]
        if len(non_blank) == 0:
            continue
        matches = non_blank.apply(lambda v: bool(number_pattern.match(str(v).strip())))
        if matches.mean() > 0.7:
            cleaned = (
                df[col]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
                .replace("", None)
            )
            try:
                df[col] = pd.to_numeric(cleaned, errors="coerce")
            except Exception:
                pass

    return df


def dataframe_to_schema(df):
    """Return a string describing the DataFrame columns, types, and sample values for Claude."""
    if df.empty:
        return "The DataFrame is empty."

    lines = [
        f"DataFrame name: df",
        f"Total rows: {len(df)}",
        f"Total columns: {len(df.columns)}",
        "",
        "Columns (name | dtype | non-null count | sample values):",
    ]
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = int(df[col].notna().sum())
        sample = df[col].dropna().astype(str).head(4).tolist()
        sample_str = ", ".join(f'"{s}"' for s in sample)
        lines.append(f'  - "{col}" | {dtype} | {non_null} non-null | samples: [{sample_str}]')

    return "\n".join(lines)


BOB_SYSTEM_PROMPT = """You are the Ringover Book of Business Bot — a helpful assistant for the Ringover US team.

You have access to a pandas DataFrame named `df` that holds the complete US Book of Business data
(roughly {row_count} rows). You must use the `query_dataframe` tool to compute ANY answer that involves:
- counts, sums, averages, or other aggregations
- filters across the data (e.g., "accounts where X and Y")
- sorting or ranking (e.g., "top N by MRR")
- looking up specific accounts or values

NEVER try to answer such questions from memory or by reading sample values — always run a query first.
You may run MULTIPLE queries if you need intermediate results.

COLUMN NAMES ARE CASE-SENSITIVE and must be quoted exactly as they appear in the schema below.
If a user's wording doesn't exactly match a column name, pick the column whose name is the closest
semantic match.

When presenting results to the user:
- Lead with the direct answer (e.g., "There are 324 accounts matching that criteria.")
- When listing accounts, show 10–20 by default and offer to expand if the list is longer
- Include relevant context columns (account name, MRR, CSM, etc.)
- Format money, counts, and percentages clearly
- Always cite the exact numbers from query results — never round or estimate

DataFrame schema:
{schema}
"""

QUERY_TOOL = {
    "name": "query_dataframe",
    "description": (
        "Evaluate a Python expression against the Book of Business pandas DataFrame. "
        "The DataFrame is available as `df`. `pd` (pandas) is also available. "
        "Use this for ALL counts, filters, sums, sorts, and lookups. "
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "A single Python expression to evaluate.",
            }
        },
        "required": ["expression"],
    },
}

def run_pandas_query(df, expression):
    """Safely evaluate a pandas expression and return a string result."""
    try:
        safe_builtins = {
            "len": len, "sum": sum, "min": min, "max": max, "sorted": sorted,
            "round": round, "abs": abs, "int": int, "float": float, "str": str,
            "list": list, "dict": dict, "set": set, "tuple": tuple, "bool": bool,
            "range": range, "enumerate": enumerate, "zip": zip, "any": any, "all": all,
        }
        result = eval(expression, {"__builtins__": safe_builtins}, {"df": df, "pd": pd})
    except Exception as e:
        return f"ERROR running expression `{expression}`: {type(e).__name__}: {e}"

    try:
        if isinstance(result, pd.DataFrame):
            if len(result) > 50:
                head = result.head(50).to_dict("records")
                return json.dumps({"total_rows": len(result), "showing_first_50": head}, default=str)
            return json.dumps(result.to_dict("records"), default=str)
        elif isinstance(result, pd.Series):
            if len(result) > 100:
                head = result.head(100).to_dict()
                return json.dumps({"total_items": len(result), "showing_first_100": head}, default=str)
            return json.dumps(result.to_dict(), default=str)
        elif isinstance(result, (int, float, str, bool)) or result is None:
            return json.dumps(result, default=str)
        elif isinstance(result, (list, dict, tuple, set)):
            if isinstance(result, set):
                result = list(result)
            return json.dumps(result, default=str)
        else:
            return str(result)
    except Exception as e:
        return f"Result computed but could not be serialized: {type(e).__name__}: {e}. repr: {repr(result)[:500]}"


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
        results = service.files().list(q=query, fields="files(id, name, mimeType)", pageSize=100).execute()
        files = results.get("files", [])

        for file in files:
            mime = file["mimeType"]
            name = file["name"]
            file_id = file["id"]

            if mime == "application/vnd.google-apps.folder":
                read_folder(file_id)
                continue

            if mime == "application/vnd.google-apps.document":
                try:
                    content = service.files().export(fileId=file_id, mimeType="text/plain").execute()
                    if isinstance(content, bytes): content = content.decode("utf-8")
                    documents.append({"name": name, "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not read this document]"})

            elif mime in ["text/plain", "text/csv", "text/markdown"]:
                try:
                    request = service.files().get_media(fileId=file_id)
                    buffer = io.BytesIO()
                    downloader = MediaIoBaseDownload(buffer, request)
                    done = False
                    while not done:
                        _, done = downloader.next_chunk()
                    content = buffer.getvalue().decode("utf-8", errors="replace")
                    documents.append({"name": name, "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not read this file]"})

            elif mime == "application/vnd.google-apps.spreadsheet":
                try:
                    content = service.files().export(fileId=file_id, mimeType="text/csv").execute()
                    if isinstance(content, bytes): content = content.decode("utf-8")
                    documents.append({"name": name, "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not read this spreadsheet]"})

            elif mime == "application/vnd.google-apps.presentation":
                try:
                    content = service.files().export(fileId=file_id, mimeType="text/plain").execute()
                    if isinstance(content, bytes): content = content.decode("utf-8")
                    documents.append({"name": name, "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not read this presentation]"})

    read_folder(folder_id)
    return documents

def documents_to_summary(documents):
    if not documents: return "No documents found in the Google Drive folder."
    summary = f"Found {len(documents)} documents in the process folder:\n\n"
    for doc in documents:
        summary += f"--- DOCUMENT: {doc['name']} ---\n"
        content = doc["content"]
        if len(content) > 15000:
            content = content[:15000] + "\n... [Document truncated due to length]"
        summary += content + "\n\n"
    return summary

PROCESS_SYSTEM_PROMPT = """You are the Ringover Process Bot — a helpful assistant for the Ringover US team.
You have access to process documents from the team's Google Drive folder.
Your job is to answer questions about company processes, procedures, and guidelines by finding
the answer in the documents provided below.
{data}
"""

# ============================================================
# SHARED: Ask Claude
# ============================================================

def ask_claude(client, question, system_prompt, chat_history):
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]
    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text

def ask_claude_with_dataframe(client, question, system_prompt, chat_history, df, max_iterations=8):
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]
    messages.append({"role": "user", "content": question})

    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=[QUERY_TOOL],
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) == "tool_use" and block.name == "query_dataframe":
                    expression = block.input.get("expression", "")
                    result_text = run_pandas_query(df, expression)
                    if len(result_text) > 20000:
                        result_text = result_text[:20000] + "\n... [truncated]"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        final_text = ""
        for block in response.content:
            if getattr(block, "type", None) == "text":
                final_text += block.text
        return final_text if final_text.strip() else "I couldn't produce an answer. Try rephrasing the question."

    return "I ran too many queries without reaching a final answer. Try simplifying the question or breaking it into parts."


# ============================================================
# LANDING PAGE
# ============================================================

def show_landing_page():
    with st.sidebar:
        show_logo(max_width_px=180)
        st.markdown("---")
        st.markdown("Select a bot from the main page to get started.")

    show_logo(max_width_px=340)

    st.markdown('<div class="landing-question">Which bot do you need to talk to?</div>', unsafe_allow_html=True)
    st.markdown('<div class="landing-subtitle">Choose a bot below to get started.</div>', unsafe_allow_html=True)

    col_left, col_us, col_gap1, col_uk, col_gap2, col_process, col_right = st.columns([0.5, 3, 0.3, 3, 0.3, 3, 0.5])

    flag_dir = os.path.dirname(__file__)
    def _load_flag_b64(filename):
        fpath = os.path.join(flag_dir, filename)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        return None

    us_flag_b64 = _load_flag_b64("flag_us.png")
    gb_flag_b64 = _load_flag_b64("flag_gb.png")

    def _flag_html(b64):
        if b64:
            return f'<div style="text-align:center; margin-bottom:0.5rem;"><img src="data:image/png;base64,{b64}" style="width:56px; border-radius:4px;" /></div>'
        return ""

    with col_us:
        st.markdown(_flag_html(us_flag_b64), unsafe_allow_html=True)
        if st.button("USA BoB Bot\n\nUS Book of Business", key="goto_bob", use_container_width=True):
            st.session_state["view"] = "bob"
            st.rerun()
        st.markdown(
            '<div style="text-align:center; color:#b8d4e3; font-size:0.9rem; margin-top:0.75rem;">'
            'US accounts, MRR, integrations, renewals'
            '</div>', unsafe_allow_html=True,
        )

    with col_uk:
        st.markdown(_flag_html(gb_flag_b64), unsafe_allow_html=True)
        if st.button("UK BoB Bot\n\nUK Book of Business", key="goto_uk_bob", use_container_width=True):
            st.session_state["view"] = "uk_bob"
            st.rerun()
        st.markdown(
            '<div style="text-align:center; color:#b8d4e3; font-size:0.9rem; margin-top:0.75rem;">'
            'UK accounts, MRR, integrations, renewals'
            '</div>', unsafe_allow_html=True,
        )

    with col_process:
        st.markdown(_flag_html(us_flag_b64), unsafe_allow_html=True)
        if st.button("Process Bot\n\nCompany Processes", key="goto_process", use_container_width=True):
            st.session_state["view"] = "process"
            st.rerun()
        st.markdown(
            '<div style="text-align:center; color:#b8d4e3; font-size:0.9rem; margin-top:0.75rem;">'
            'Procedures, guidelines, how-tos'
            '</div>', unsafe_allow_html=True,
        )


# ============================================================
# BOT VIEW (shared logic for BoB + Process)
# ============================================================

def show_bot_view(bot_mode, config):
    # 1. Setup our variables
    data, documents, df = None, None, None
    connection_ok, connection_error = False, None

    if bot_mode == "uk_bob":
        sheet_id = config.get("uk_google_sheet_id", "")
        sheet_gid = config.get("uk_google_sheet_gid", "")
        sheet_tab = config.get("uk_google_sheet_tab_name", "")
        currency_symbol, region_label = "£", "UK"
    elif bot_mode == "bob":
        sheet_id = config.get("google_sheet_id", "")
        sheet_gid = config.get("google_sheet_gid", "")
        sheet_tab = config.get("google_sheet_tab_name", "")
        currency_symbol, region_label = "$", "US"
    else:
        region_label, currency_symbol, loaded_tab, all_tabs = "", "", "", []

    # 2. DRAW THE SIDEBAR FIRST (so it doesn't vanish while data loads)
    with st.sidebar:
        show_logo(max_width_px=180)

        if st.button("← Back to Home", key="back_home", use_container_width=True):
            st.session_state["view"] = "landing"
            st.rerun()

        st.markdown("---")
        st.markdown("### 📡 Connection Status")
        
        # Create an empty box in the sidebar to hold our loading spinner/status
        status_placeholder = st.empty()

        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        if bot_mode == "bob":
            st.markdown("### 💡 Example Questions")
            st.markdown("""
- Which accounts have Bullhorn integrated?
- List all platinum accounts with their MRR
- Who are the top 10 accounts by MRR?
- Which accounts are up for renewal?
- How many accounts does each CSM manage?
            """)
        elif bot_mode == "uk_bob":
            st.markdown("### 💡 Example Questions")
            st.markdown("""
- Who are the top 10 UK accounts by MRR?
- Which UK accounts have an ATS/CRM integrated?
- List all UK accounts up for renewal
- What is the total UK MRR?
            """)
        else:
            st.markdown("### 💡 Example Questions")
            st.markdown("""
- What is the process for client onboarding?
- How do we handle an escalation?
- What are the steps for a renewal?
- What is our SLA for support tickets?
            """)

    # 3. NOW LOAD THE DATA (while showing a spinner in our placeholder)
    with status_placeholder.container():
        with st.spinner("Connecting to Google..."):
            if bot_mode in ("bob", "uk_bob"):
                try:
                    data, loaded_tab, all_tabs = load_sheet_data(
                        config["google_credentials"], sheet_id, sheet_gid, sheet_tab
                    )
                    df = data_to_dataframe(data)
                    connection_ok = True
                except Exception as e:
                    connection_error = str(e)
            else:
                try:
                    documents = load_drive_documents(config["google_credentials"], config["google_drive_folder_id"])
                    connection_ok = True
                except Exception as e:
                    connection_error = str(e)

    # 4. OVERWRITE THE SPINNER WITH THE FINAL STATUS
    with status_placeholder.container():
        if bot_mode in ("bob", "uk_bob"):
            if connection_ok and df is not None:
                st.markdown(f'<span class="status-connected">✅ Connected to {region_label} Google Sheet</span>', unsafe_allow_html=True)
                st.markdown(f"**Accounts loaded:** {len(df)}")
                
                mrr_col = next((c for c in df.columns if "total mrr" in c.lower()), None)
                if mrr_col and pd.api.types.is_numeric_dtype(df[mrr_col]):
                    total_mrr = df[mrr_col].sum()
                    st.markdown(f"**Total MRR:** {currency_symbol}{total_mrr:,.2f}")
            else:
                st.markdown(f'<span class="status-error">❌ Could not connect...</span>', unsafe_allow_html=True)
                if connection_error: st.error(connection_error)
        else:
            if connection_ok and documents is not None:
                st.markdown(f'<span class="status-connected">✅ Connected to Google Drive</span>', unsafe_allow_html=True)
                st.markdown(f"**Documents loaded:** {len(documents)}")
            else:
                st.markdown(f'<span class="status-error">❌ Could not connect...</span>', unsafe_allow_html=True)
                if connection_error: st.error(connection_error)

    # 5. RENDER THE MAIN CHAT UI
    if bot_mode == "bob":
        st.markdown('<div class="main-header">USA Book of Business Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask me anything about the US Book of Business.</div>', unsafe_allow_html=True)
    elif bot_mode == "uk_bob":
        st.markdown('<div class="main-header">UK Book of Business Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask me anything about the UK Book of Business.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="main-header">📋 Process Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask me anything about Ringover processes, procedures, and guidelines.</div>', unsafe_allow_html=True)

    # Chat history
    current_key = f"{bot_mode}_messages"
    if current_key not in st.session_state:
        st.session_state[current_key] = []

    for message in st.session_state[current_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    placeholder = f"Ask me about the {region_label} Book of Business..." if bot_mode in ("bob", "uk_bob") else "Ask me about a process..."

    if not connection_ok:
        st.warning(f"⚠️ Could not connect to the data source. Check your secrets and click **Refresh Data**.")

    if prompt := st.chat_input(placeholder):
        if not connection_ok:
            st.error("Cannot process questions without a data connection.")
            st.stop()
        
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state[current_key].append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    claude_client = anthropic.Anthropic(api_key=config["anthropic_api_key"])
                    if bot_mode in ("bob", "uk_bob"):
                        schema = dataframe_to_schema(df)
                        system = BOB_SYSTEM_PROMPT.replace("US team", f"{region_label} team").replace("US Book of Business", f"{region_label} Book of Business").format(row_count=len(df), schema=schema)
                        response = ask_claude_with_dataframe(claude_client, prompt, system, st.session_state[current_key][:-1], df)
                    else:
                        doc_summary = documents_to_summary(documents)
                        system = PROCESS_SYSTEM_PROMPT.format(data=doc_summary)
                        response = ask_claude(claude_client, prompt, system, st.session_state[current_key][:-1])

                    st.markdown(response)
                    st.session_state[current_key].append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

# ============================================================
# MAIN APP
# ============================================================

def main():
    config = load_credentials()

    # 1. Wait here until the correct password is entered
    if not check_password(config["app_password"]):
        st.stop()

    # 2. Set the default page to "landing" so it doesn't crash
    if "view" not in st.session_state:
        st.session_state["view"] = "landing"

    # 3. Read which page we should be on
    view = st.session_state["view"]

    # 4. Route the user to the correct page
    if view == "landing":
        show_landing_page()
    elif view == "bob":
        show_bot_view("bob", config)
    elif view == "uk_bob":
        show_bot_view("uk_bob", config)
    elif view == "process":
        show_bot_view("process", config)
    else:
        st.session_state["view"] = "landing"
        st.rerun()

if __name__ == "__main__":
    main()
