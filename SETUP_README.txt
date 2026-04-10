============================================================
  RINGOVER BOOK OF BUSINESS BOT - SETUP INSTRUCTIONS
  Follow these steps EXACTLY in order
============================================================

STEP 1: OPEN TERMINAL
---------------------
- On Mac: Press Command + Space, type "Terminal", press Enter
- On Windows: Press the Windows key, type "Command Prompt", press Enter

You should see a window with a blinking cursor. This is where
you will type commands.


STEP 2: NAVIGATE TO THE BOT FOLDER
-----------------------------------
You need to tell Terminal where your bot files are.

If you saved the ringover-bots folder to your Desktop:

  Mac:     cd ~/Desktop/ringover-bots
  Windows: cd %USERPROFILE%\Desktop\ringover-bots

If it is somewhere else, type: cd [path to your ringover-bots folder]

TIP: On Mac, you can type "cd " (with a space after it) and then
drag the ringover-bots folder from Finder into the Terminal window.
It will auto-fill the path for you.


STEP 3: CREATE A VIRTUAL ENVIRONMENT
--------------------------------------
Type this command and press Enter:

  Mac:     python3 -m venv venv
  Windows: python -m venv venv

Then activate it:

  Mac:     source venv/bin/activate
  Windows: venv\Scripts\activate

You should see (venv) appear at the beginning of your command line.
That means it is working.


STEP 4: INSTALL THE REQUIRED PACKAGES
--------------------------------------
Type this command and press Enter:

  pip install -r requirements.txt

Wait for it to finish. You will see a bunch of text scrolling by.
When it is done, you will see the blinking cursor again.


STEP 5: ADD YOUR CREDENTIALS FILE
-----------------------------------
Move your Google service account JSON file (credentials.json) into
the ringover-bots folder. If it has a different name, rename it to:

  credentials.json


STEP 6: CREATE YOUR SECRETS FILE
----------------------------------
This is where you put your API keys. The bot reads this file on startup.

A) Create the secrets folder. Type:

  Mac:     mkdir -p .streamlit
  Windows: mkdir .streamlit

B) Create the secrets file.

  Mac:     nano .streamlit/secrets.toml
  Windows: notepad .streamlit\secrets.toml

C) Paste the following into the file, replacing the placeholder values:

[secrets]
ANTHROPIC_API_KEY = "sk-ant-PASTE-YOUR-REAL-KEY-HERE"
GOOGLE_SHEET_ID = "1kMIcEWuZduGDPMqvIl8_GC9JzYGB2kb4NQtNzVcBby4"
GOOGLE_CREDENTIALS_JSON = '''PASTE-YOUR-ENTIRE-JSON-FILE-CONTENTS-HERE'''

IMPORTANT: For the GOOGLE_CREDENTIALS_JSON line, you need to:
  1. Open your credentials.json file in a text editor
  2. Select ALL of the text (Command+A on Mac, Ctrl+A on Windows)
  3. Copy it (Command+C or Ctrl+C)
  4. Paste it between the triple quotes ''' ... '''

  It will look something like:
  GOOGLE_CREDENTIALS_JSON = '''{"type": "service_account", "project_id": "your-project", ...}'''

D) Save the file:
  Mac (nano):  Press Ctrl+O, then Enter, then Ctrl+X
  Windows:     Press Ctrl+S, then close Notepad


STEP 7: RUN THE BOT
---------------------
Type this command and press Enter:

  streamlit run app.py

After a moment, you should see something like:

  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501

Your web browser should open automatically. If it does not,
copy that URL and paste it into your browser.

You should see the Ringover Book of Business Bot with a chat
interface. Try asking: "How many accounts are in the data?"


STEP 8: STOPPING THE BOT
--------------------------
To stop the bot, go back to Terminal and press Ctrl+C.


============================================================
  TROUBLESHOOTING
============================================================

"ModuleNotFoundError":
  Make sure you activated the virtual environment (Step 3)
  and installed packages (Step 4).

"Could not load credentials":
  Check that your .streamlit/secrets.toml file exists and
  has the correct values. Make sure quotes are correct.

"Could not connect to Google Sheet":
  Make sure you shared the Google Sheet with your service
  account email address (the one ending in
  @your-project.iam.gserviceaccount.com).

"AuthenticationError" from Anthropic:
  Double-check your ANTHROPIC_API_KEY in secrets.toml.
  Make sure you copied the full key starting with sk-ant-.

The bot says "0 accounts loaded":
  Make sure the Google Sheet has data in the first sheet tab
  and that row 1 contains column headers.

============================================================
