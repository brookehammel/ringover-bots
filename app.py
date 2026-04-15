import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import anthropic
import json
import csv
import io

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

# --- Styling ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #2E5090;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .status-connected { color: #4CAF50; font-weight: 600; }
    .status-error { color: #f44336; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# --- Load Credentials ---
def load_credentials():
    """Load API keys and settings from Streamlit secrets or secrets.toml."""
    try:
        # BOT_MODE controls which bot(s) this deployment shows:
        #   "both" = show toggle for both bots (default)
        #   "bob_only" = only show the Book of Business Bot
        #   "process_only" = only show the Process Bot
        bot_mode = st.secrets["secrets"].get("BOT_MODE", "both").lower().strip()

        config = {
            "anthropic_api_key": st.secrets["secrets"]["ANTHROPIC_API_KEY"],
            "google_sheet_id": st.secrets["secrets"].get("GOOGLE_SHEET_ID", ""),
            "google_drive_folder_id": st.secrets["secrets"].get("GOOGLE_DRIVE_FOLDER_ID", ""),
            "google_credentials": json.loads(st.secrets["secrets"]["GOOGLE_CREDENTIALS_JSON"]),
            "bot_mode": bot_mode,
        }
        return config
    except Exception as e:
        st.error(f"Could not load credentials. Make sure your secrets are set up correctly. Error: {e}")
        st.stop()


# --- Google Auth Helper ---
def get_google_creds(credentials_info):
    """Create Google credentials with both Sheets and Drive access."""
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
    """Connect to Google Sheets and read the Book of Business data."""
    creds = get_google_creds(_credentials)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_records()
    return data


def data_to_summary(data):
    """Create a concise summary of the data for the AI, including all rows as CSV."""
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
    """Read all documents from a Google Drive folder."""
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

            # Recurse into subfolders
            if mime == "application/vnd.google-apps.folder":
                read_folder(file_id)
                continue

            # Read Google Docs
            if mime == "application/vnd.google-apps.document":
                try:
                    content = service.files().export(
                        fileId=file_id, mimeType="text/plain"
                    ).execute()
                    if isinstance(content, bytes):
                        content = content.decode("utf-8")
                    documents.append({"name": name, "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not read this document]"})

            # Read text files, PDFs (as text), etc.
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

            # Read Google Sheets as CSV
            elif mime == "application/vnd.google-apps.spreadsheet":
                try:
                    content = service.files().export(
                        fileId=file_id, mimeType="text/csv"
                    ).execute()
                    if isinstance(content, bytes):
                        content = content.decode("utf-8")
                    documents.append({"name": name, "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not read this spreadsheet]"})

            # Read Google Slides as text
            elif mime == "application/vnd.google-apps.presentation":
                try:
                    content = service.files().export(
                        fileId=file_id, mimeType="text/plain"
                    ).execute()
                    if isinstance(content, bytes):
                        content = content.decode("utf-8")
                    documents.append({"name": name, "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not read this presentation]"})

            # Handle shortcuts by resolving to actual file
            elif mime == "application/vnd.google-apps.shortcut":
                try:
                    shortcut_details = service.files().get(
                        fileId=file_id, fields="shortcutDetails"
                    ).execute()
                    target_id = shortcut_details.get("shortcutDetails", {}).get("targetId")
                    target_mime = shortcut_details.get("shortcutDetails", {}).get("targetMimeType", "")

                    if target_id:
                        if target_mime == "application/vnd.google-apps.document":
                            content = service.files().export(
                                fileId=target_id, mimeType="text/plain"
                            ).execute()
                            if isinstance(content, bytes):
                                content = content.decode("utf-8")
                            documents.append({"name": name + " (shortcut)", "content": content})
                        elif target_mime == "application/vnd.google-apps.folder":
                            read_folder(target_id)
                        elif target_mime == "application/vnd.google-apps.spreadsheet":
                            content = service.files().export(
                                fileId=target_id, mimeType="text/csv"
                            ).execute()
                            if isinstance(content, bytes):
                                content = content.decode("utf-8")
                            documents.append({"name": name + " (shortcut)", "content": content})
                        elif target_mime == "application/vnd.google-apps.presentation":
                            content = service.files().export(
                                fileId=target_id, mimeType="text/plain"
                            ).execute()
                            if isinstance(content, bytes):
                                content = content.decode("utf-8")
                            documents.append({"name": name + " (shortcut)", "content": content})
                except Exception:
                    documents.append({"name": name, "content": "[Could not resolve this shortcut]"})

    read_folder(folder_id)
    return documents


def documents_to_summary(documents):
    """Format documents for the AI."""
    if not documents:
        return "No documents found in the Google Drive folder."

    summary = f"Found {len(documents)} documents in the process folder:\n\n"
    for doc in documents:
        summary += f"--- DOCUMENT: {doc['name']} ---\n"
        # Truncate very long documents to avoid token limits
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
    """Send the question and data to Claude and get an answer."""
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
# MAIN APP
# ============================================================

def main():
    # Load credentials
    config = load_credentials()

    # Determine which bot(s) to show based on BOT_MODE setting
    deploy_mode = config["bot_mode"]
    if deploy_mode == "bob_only":
        bot_mode = "📊 Book of Business Bot"
        show_toggle = False
    elif deploy_mode == "process_only":
        bot_mode = "📋 Process Bot"
        show_toggle = False
    else:
        bot_mode = None  # Will be set by toggle below
        show_toggle = True

    # Sidebar - Bot Selection (only if both bots are enabled)
    with st.sidebar:
        if show_toggle:
            st.markdown("### 🤖 Choose Your Bot")
            bot_mode = st.radio(
                "Which bot do you want to talk to?",
                ["📊 Book of Business Bot", "📋 Process Bot"],
                index=0,
                label_visibility="collapsed"
            )
            st.markdown("---")

        st.markdown("### 📡 Connection Status")

        if bot_mode == "📊 Book of Business Bot":
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

        # Refresh button
        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        if bot_mode == "📊 Book of Business Bot":
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

    # Header changes based on bot mode
    if bot_mode == "📊 Book of Business Bot":
        st.markdown('<div class="main-header">📊 Ringover Book of Business Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask me anything about the US Book of Business — accounts, MRR, integrations, renewals, and more.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="main-header">📋 Ringover Process Bot</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Ask me anything about Ringover processes, procedures, and guidelines.</div>', unsafe_allow_html=True)

    # Use separate chat histories for each bot
    bob_key = "bob_messages"
    process_key = "process_messages"

    if bob_key not in st.session_state:
        st.session_state[bob_key] = []
    if process_key not in st.session_state:
        st.session_state[process_key] = []

    current_key = bob_key if bot_mode == "📊 Book of Business Bot" else process_key

    # Display chat history
    for message in st.session_state[current_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    placeholder = "Ask me about the Book of Business..." if bot_mode == "📊 Book of Business Bot" else "Ask me about a process or procedure..."

    if prompt := st.chat_input(placeholder):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state[current_key].append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Looking through the data..." if bot_mode == "📊 Book of Business Bot" else "Searching the documents..."):
                try:
                    claude_client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

                    if bot_mode == "📊 Book of Business Bot":
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


if __name__ == "__main__":
    main()
