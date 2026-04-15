import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import anthropic
import json
import csv
import io
import base64
import os

# ============================================================
# RINGOVER BOTS
# Book of Business Bot & Process Bot
# ============================================================

# --- Page Configuration ---
st.set_page_config(
    page_title="Ringover Bots",
    page_icon="🤖",
    layout="wide"
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

    /* Hide the default Streamlit header/footer branding */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}
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
            "google_sheet_id": st.secrets["secrets"].get("GOOGLE_SHEET_ID", ""),
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
def load_sheet_data(_credentials, sheet_id):
    creds = get_google_creds(_credentials)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_records()
    return data


def data_to_summary(data):
    if not data:
        return "No data found in the spreadsheet."

    columns = list(data[0].keys())
    total_rows = len(data)

    summary = f"This Google Sheet contains {total_rows} accounts with the following columns:\n"
    summary += ", ".join(columns) + "\n\n"

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    csv_text = output.getvalue()

    summary += "Here is the complete data:\n\n"
    summary += csv_text

    return summary


BOB_SYSTEM_PROMPT = """You are the Ringover Book of Business Bot — a helpful assistant for the Ringover US team.
You have access to the complete US Book of Business data from a live Google Sheet.

Your job is to answer questions about the accounts, provide lists, pull reports, and help the team
find information quickly without having to search through the spreadsheet manually.

IMPORTANT RULES:
- Always base your answers on the actual data provided below. Never make up information.
- When listing accounts, format them clearly and include relevant details.
- When asked for counts or totals, be precise.
- If you are not sure about something, say so rather than guessing.
- When asked about MRR, licenses, or financial data, be exact with the numbers.
- If someone asks a question the data cannot answer, let them know what IS available.
- Be conversational and helpful. These are your colleagues.
- When providing lists, include enough context to be useful (e.g., Team Name, MRR, CSM, etc.)
- If the data has blank or empty values for a field, mention that the field is empty for those accounts.

HERE IS THE CURRENT DATA FROM THE GOOGLE SHEET:
{data}
"""


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
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=100
        ).execute()
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
                    if isinstance(content, bytes):
                        content = content.decode("utf-8")
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
                    if isinstance(content, bytes):
                        content = content.decode("utf-8")
                    documents.append({"name": name, "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not read this spreadsheet]"})

            elif mime == "application/vnd.google-apps.presentation":
                try:
                    content = service.files().export(fileId=file_id, mimeType="text/plain").execute()
                    if isinstance(content, bytes):
                        content = content.decode("utf-8")
                    documents.append({"name": name, "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not read this presentation]"})

            elif mime == "application/vnd.google-apps.shortcut":
                try:
                    shortcut_details = service.files().get(fileId=file_id, fields="shortcutDetails").execute()
                    target_id = shortcut_details.get("shortcutDetails", {}).get("targetId")
                    target_mime = shortcut_details.get("shortcutDetails", {}).get("targetMimeType", "")

                    if target_id:
                        if target_mime == "application/vnd.google-apps.document":
                            content = service.files().export(fileId=target_id, mimeType="text/plain").execute()
                            if isinstance(content, bytes):
                                content = content.decode("utf-8")
                            documents.append({"name": name + " (shortcut)", "content": content})
                        elif target_mime == "application/vnd.google-apps.folder":
                            read_folder(target_id)
                        elif target_mime == "application/vnd.google-apps.spreadsheet":
                            content = service.files().export(fileId=target_id, mimeType="text/csv").execute()
                            if isinstance(content, bytes):
                                content = content.decode("utf-8")
                            documents.append({"name": name + " (shortcut)", "content": content})
                        elif target_mime == "application/vnd.google-apps.presentation":
                            content = service.files().export(fileId=target_id, mimeType="text/plain").execute()
                            if isinstance(content, bytes):
                                content = content.decode("utf-8")
                            documents.append({"name": name + " (shortcut)", "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not resolve this shortcut]"})

    read_folder(folder_id)
    return documents


def documents_to_summary(documents):
    if not documents:
        return "No documents found in the Google Drive folder."

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

IMPORTANT RULES:
- Always base your answers on the actual documents provided below. Never make up processes or procedures.
- When you find an answer, tell the user which document it came from (e.g., "According to the Client Onboarding doc...").
- If the answer spans multiple documents, reference all of them.
- If you cannot find the answer in any document, say so clearly and suggest which type of document might contain the answer.
- Be conversational and helpful. These are your colleagues.
- If a process has specific steps, list them clearly in order.
- If you notice conflicting information between documents, flag it to the user.

HERE ARE THE CURRENT PROCESS DOCUMENTS:
{data}
"""


# ============================================================
# SHARED: Ask Claude
# ============================================================

def ask_claude(client, question, system_prompt, chat_history):
    messages = []
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    )

    return response.content[0].text


# ============================================================
# LANDING PAGE
# ============================================================

def show_landing_page():
    show_logo(max_width_px=340)

    st.markdown('<div class="landing-question">Which bot do you need to talk to?</div>', unsafe_allow_html=True)
    st.markdown('<div class="landing-subtitle">Choose a bot below to get started.</div>', unsafe_allow_html=True)

    col_left, col_bob, col_gap, col_process, col_right = st.columns([1, 3, 0.4, 3, 1])

    with col_bob:
        if st.button("📊  BoB Bot\n\nBook of Business", key="goto_bob", use_container_width=True):
            st.session_state["view"] = "bob"
            st.rerun()
        st.markdown(
            '<div style="text-align:center; color:#b8d4e3; font-size:0.9rem; margin-top:0.75rem;">'
            'Accounts, MRR, integrations, renewals'
            '</div>',
            unsafe_allow_html=True,
        )

    with col_process:
        if st.button("📋  Process Bot\n\nCompany Processes", key="goto_process", use_container_width=True):
            st.session_state["view"] = "process"
            st.rerun()
        st.markdown(
            '<div style="text-align:center; color:#b8d4e3; font-size:0.9rem; margin-top:0.75rem;">'
            'Procedures, guidelines, how-tos'
            '</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# BOT VIEW (shared logic for BoB + Process)
# ============================================================

def show_bot_view(bot_mode, config):
    # Sidebar
    with st.sidebar:
        show_logo(max_width_px=180)

        if st.button("← Back to Home", key="back_home", use_container_width=True):
            st.session_state["view"] = "landing"
            st.rerun()

        st.markdown("---")
        st.markdown("### 📡 Connection Status")

        data = None
        documents = None

        if bot_mode == "bob":
            try:
                data = load_sheet_data(config["google_credentials"], config["google_sheet_id"])
                st.markdown(f'<span class="status-connected">✅ Connected to Google Sheet</span>', unsafe_allow_html=True)
                st.markdown(f"**Accounts loaded:** {len(data)}")

                if data:
                    columns = list(data[0].keys())
                    st.markdown(f"**Data columns:** {len(columns)}")
                    mrr_values = [row.get("Total MRR", 0) for row in data if row.get("Total MRR")]
                    if mrr_values:
                        numeric_mrr = []
                        for v in mrr_values:
                            try:
                                numeric_mrr.append(float(str(v).replace("$", "").replace(",", "")))
                            except (ValueError, TypeError):
                                pass
                        if numeric_mrr:
                            total_mrr = sum(numeric_mrr)
                            st.markdown(f"**Total MRR:** ${total_mrr:,.2f}")
            except Exception as e:
                st.markdown(f'<span class="status-error">❌ Could not connect to Google Sheet</span>', unsafe_allow_html=True)
                st.error(f"Error: {e}")
                st.stop()
        else:
            try:
                documents = load_drive_documents(config["google_credentials"], config["google_drive_folder_id"])
                st.markdown(f'<span class="status-connected">✅ Connected to Google Drive</span>', unsafe_allow_html=True)
                st.markdown(f"**Documents loaded:** {len(documents)}")
                if documents:
                    st.markdown("**Documents found:**")
                    for doc in documents:
                        st.markdown(f"- {doc['name']}")
            except Exception as e:
                st.markdown(f'<span class="status-error">❌ Could not connect to Google Drive</span>', unsafe_allow_html=True)
                st.error(f"Error: {e}")
                st.stop()

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
- What is the total MRR by business unit?
- Show me all accounts with Empower licenses
            """)
        else:
            st.markdown("### 💡 Example Questions")
            st.markdown("""
- What is the process for client onboarding?
- How do we handle an escalation?
- What are the steps for a renewal?
- What is our SLA for support tickets?
- How do I submit a feature request?
            """)

    # Main area header
    if bot_mode == "bob":
        st.markdown('<div class="main-header">📊 Book of Business Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask me anything about the US Book of Business — accounts, MRR, integrations, renewals, and more.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="main-header">📋 Process Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask me anything about Ringover processes, procedures, and guidelines.</div>', unsafe_allow_html=True)

    # Chat history
    bob_key = "bob_messages"
    process_key = "process_messages"

    if bob_key not in st.session_state:
        st.session_state[bob_key] = []
    if process_key not in st.session_state:
        st.session_state[process_key] = []

    current_key = bob_key if bot_mode == "bob" else process_key

    for message in st.session_state[current_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    placeholder = "Ask me about the Book of Business..." if bot_mode == "bob" else "Ask me about a process or procedure..."

    if prompt := st.chat_input(placeholder):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state[current_key].append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Looking through the data..." if bot_mode == "bob" else "Searching the documents..."):
                try:
                    claude_client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

                    if bot_mode == "bob":
                        data_summary = data_to_summary(data)
                        system = BOB_SYSTEM_PROMPT.format(data=data_summary)
                    else:
                        doc_summary = documents_to_summary(documents)
                        system = PROCESS_SYSTEM_PROMPT.format(data=doc_summary)

                    response = ask_claude(
                        claude_client,
                        prompt,
                        system,
                        st.session_state[current_key][:-1],
                    )
                    st.markdown(response)
                    st.session_state[current_key].append({"role": "assistant", "content": response})
                except anthropic.AuthenticationError:
                    st.error("Your Anthropic API key is invalid. Please check your secrets.")
                except Exception as e:
                    st.error(f"Something went wrong: {e}")


# ============================================================
# MAIN APP
# ============================================================

def main():
    config = load_credentials()

    if not check_password(config["app_password"]):
        st.stop()

    # Track which view we're on
    if "view" not in st.session_state:
        st.session_state["view"] = "landing"

    view = st.session_state["view"]

    if view == "landing":
        show_landing_page()
    elif view == "bob":
        show_bot_view("bob", config)
    elif view == "process":
        show_bot_view("process", config)
    else:
        st.session_state["view"] = "landing"
        st.rerun()


if __name__ == "__main__":
    main()
