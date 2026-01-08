# googlesheet_campaign1.py
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -----------------------------
# Google Sheets Setup
# -----------------------------
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDS = Credentials.from_service_account_file(
    "ServiceAccount.json",  # Path to your Service Account JSON
    scopes=SCOPE
)

client = gspread.authorize(CREDS)

SPREADSHEET_NAME = "ChatBotData"
WORKSHEET_NAME = "Campaign1"

# Columns: match your chatbot session data + tracking
HEADERS = [
    "Name",
    "Date of Birth",
    "Age",
    "Life Stage",
    "Dependents",
    "Protection Level",
    "Monthly Budget",
    "Income",
    "Phone",
    "Email",
    "Timestamp",
    "Whatsapp",      # Swapped position
    "Email_sent"     # Swapped position
]

# -----------------------------
# Initialize Sheet
# -----------------------------
def init_sheet():
    """Ensure spreadsheet, worksheet, and headers exist."""
    try:
        sh = client.open(SPREADSHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sh = client.create(SPREADSHEET_NAME)

    try:
        sheet = sh.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        sheet = sh.add_worksheet(
            title=WORKSHEET_NAME,
            rows=1000,
            cols=len(HEADERS)
        )

    all_values = sheet.get_all_values()
    if not all_values:
        sheet.append_row(HEADERS)

    return sheet

# -----------------------------
# Helper: Get column index by header
# -----------------------------
def get_col_index(sheet, header_name):
    """Return 1-based column index for a given header name."""
    headers = sheet.row_values(1)
    if header_name in headers:
        return headers.index(header_name) + 1
    return None

# -----------------------------
# Generate WhatsApp Link
# -----------------------------
def generate_whatsapp_link(phone):
    if not phone:
        return ""
    phone_clean = ''.join(filter(str.isdigit, str(phone)))
    return f"https://wa.me/{phone_clean}"

# -----------------------------
# Save Chatbot Session
# -----------------------------
def save_session(session_data, email_sent=False):
    """
    Append a new row for the chatbot session.
    `session_data` is a dict containing the user responses.
    """
    sheet = init_sheet()

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    email_ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S") if email_sent else ""
    wa_link = generate_whatsapp_link(session_data.get("phone", ""))

    # Format income with RM
    income_raw = session_data.get("income", "")
    if income_raw:
        try:
            income_val = float(income_raw)
            income_str = f"RM {income_val:,.2f}"  # RM 1,234.56
        except ValueError:
            income_str = f"RM {income_raw}"       # fallback if not a number
    else:
        income_str = ""

    # Format Monthly Budget with RM (optional, same as Income)
    budget_raw = session_data.get("budget", "")
    if budget_raw:
        try:
            budget_val = float(budget_raw)
            budget_str = f"RM {budget_val:,.2f}"
        except ValueError:
            budget_str = f"RM {budget_raw}"
    else:
        budget_str = ""

    row = [
        session_data.get("name", ""),
        session_data.get("dob", ""),
        session_data.get("age", ""),
        session_data.get("life_stage", ""),
        session_data.get("dependents", ""),
        session_data.get("protection_level", ""),
        budget_str,   # <- Monthly Budget formatted
        income_str,   # <- Income formatted
        session_data.get("phone", ""),
        session_data.get("email", ""),
        timestamp,    # Timestamp
        wa_link,      # Whatsapp link
        email_ts      # Email_sent
    ]

    all_values = sheet.get_all_values()
    next_row = len(all_values) + 1
    sheet.insert_row(row, next_row)
    print(f"[Google Sheets] Row added for {session_data.get('name', '')} at row {next_row}")

    # -----------------------------------------
    # Auto-send email (if email provided)
    # -----------------------------------------
    email = session_data.get("email", "") or ""
    email = email.strip()
    if email:
        try:
            # import locally to avoid import-time side-effects
            from Emailservice import build_email_html, send_email, update_email_sent as es_update
            # prepare a row dict so the Emailservice template can read values
            row_dict = {
                "Name": session_data.get("name", ""),
                "Age": session_data.get("age", ""),
                "LifeStage": session_data.get("life_stage", ""),
                "Life Stage": session_data.get("life_stage", ""),
                "Dependents": session_data.get("dependents", ""),
                "ProtectionLevel": session_data.get("protection_level", ""),
                "Protection Level": session_data.get("protection_level", ""),
                "MonthlyBudget": session_data.get("budget", ""),
                "Monthly Budget": session_data.get("budget", ""),
                "Income": income_str,
                "Phone": session_data.get("phone", ""),
                "Whatsapp": wa_link,
                "Email": email
            }
            subject = "Your Personalised Income Protection Summary"
            html = build_email_html(row_dict)
            send_email(email, subject, html)
            # update timestamp in sheet row
            try:
                es_update(sheet, next_row)
            except Exception:
                # fallback: update by email finder
                update_email_sent(email)
            print(f"[Email] Sent summary to {email}")
        except Exception as e:
            print(f"[Email] Failed to send email to {email}: {e}")

    return session_data.get("email")  # For optional email updates

# -----------------------------
# Update Email_sent timestamp
# -----------------------------
def update_email_sent(email):
    """Update Email_sent timestamp for a specific email."""
    sheet = init_sheet()
    email_col = get_col_index(sheet, "Email")
    email_sent_col = get_col_index(sheet, "Email_sent")

    if not email_col or not email_sent_col:
        print("[Google Sheets] Header Email or Email_sent not found.")
        return

    all_values = sheet.get_all_values()
    for idx, row in enumerate(all_values, start=1):
        if len(row) >= email_col and row[email_col - 1].strip() == email.strip():
            email_ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            sheet.update_cell(idx, email_sent_col, email_ts)
            print(f"[Google Sheets] Email_sent timestamp updated at row {idx}")
            return

    print(f"[Google Sheets] No matching email found to update Email_sent for {email}.")
