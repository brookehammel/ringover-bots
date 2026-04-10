import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import anthropic
import json
import csv
import io

# ============================================================
# RINGOVER BOOK OF BUSINESS BOT
# A conversational assistant for querying the US Book of Business
# ============================================================

# --- Page Configuration ---
st.set_page_config(
    page_title="Ringover Book of Business Bot",
    page_icon="📊",
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
        config = {
            "anthropic_api_key": st.secrets["secrets"]["ANTHROPIC_API_KEY"],
            "google_sheet_id": st.secrets["secrets"]["GOOGLE_SHEET_ID"],
            "google_credentials": json.loads(st.secrets["secrets"]["GOOGLE_CREDENTIALS_JSON"]),
        }
        return config
    except Exception as e:
        st.error(f"Could not load credentials. Make sure your .streamlit/secrets.toml file is set up correctly. Error: {e}")
        st.stop()


# --- Connect to Google Sheet ---
@st.cache_data(ttl=300)  # Cache for 5 minutes, then refresh
def load_sheet_data(_credentials, sheet_id):
    """Connect to Google Sheets and read the Book of Business data."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(_credentials, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1  # Reads the first sheet
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

    # Convert all data to CSV format so the AI can search through it
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    csv_text = output.getvalue()

    summary += "Here is the complete data:\n\n"
    summary += csv_text

    return summary


def ask_claude(client, question, data_summary, chat_history):
    """Send the question and data to Claude and get an answer."""
    system_prompt = f"""You are the Ringover Book of Business Bot — a helpful assistant for the Ringover US team.
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
{data_summary}
"""

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


# --- Main App ---
def main():
    # Header
    st.markdown('<div class="main-header">📊 Ringover Book of Business Bot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask me anything about the US Book of Business — accounts, MRR, integrations, renewals, and more.</div>', unsafe_allow_html=True)

    # Load credentials
    config = load_credentials()

    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")

        # Connection status
        st.markdown("---")
        st.markdown("### 📡 Connection Status")

        # Try to load data
        try:
            data = load_sheet_data(config["google_credentials"], config["google_sheet_id"])
            st.markdown(f'<span class="status-connected">✅ Connected to Google Sheet</span>', unsafe_allow_html=True)
            st.markdown(f"**Accounts loaded:** {len(data)}")

            # Show some quick stats
            if data:
                columns = list(data[0].keys())
                st.markdown(f"**Data columns:** {len(columns)}")

                # Quick stats if MRR column exists
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

        # Refresh button
        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
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

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask me about the Book of Business..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Looking through the data..."):
                try:
                    claude_client = anthropic.Anthropic(api_key=config["anthropic_api_key"])
                    data_summary = data_to_summary(data)
                    response = ask_claude(
                        claude_client,
                        prompt,
                        data_summary,
                        st.session_state.messages[:-1],  # Exclude the message we just added
                    )
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except anthropic.AuthenticationError:
                    st.error("Your Anthropic API key is invalid. Please check your secrets.toml file.")
                except Exception as e:
                    st.error(f"Something went wrong: {e}")


if __name__ == "__main__":
    main()
