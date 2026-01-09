# emailservice.py
# Auto-send personalised summary email using Google Sheets data
# Modern 2025-style email UI with fixed WhatsApp number
# Includes PDF attachment: Benefits.pdf
# UTF-8 safe for emojis and special characters

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
import os

# -------------------------------------------------
# GMAIL SMTP CONFIG
# -------------------------------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_USERNAME = "kkmjpaibot@gmail.com"       # 🔴 CHANGE
SMTP_PASSWORD = "boch kenq tanl jxhr"        # 🔴 CHANGE

SENDER_NAME = "Erica – Income Protection Advisor"

# -------------------------------------------------
# GOOGLE SHEETS CONFIG
# -------------------------------------------------
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDS = Credentials.from_service_account_file(
    "ServiceAccount.json",
    scopes=SCOPE
)

client = gspread.authorize(CREDS)

SPREADSHEET_NAME = "ChatBotData"
WORKSHEET_NAME = "Campaign1"

# -------------------------------------------------
# HELPER: Safe value getter (improved)
# -------------------------------------------------
def v(row, key):
    """Robust getter: try multiple variants and do case-insensitive matching."""
    if not row:
        return "—"
    if key in row and row.get(key):
        return row.get(key)
    def norm(s): return str(s).lower().replace(" ", "").replace("_", "")
    target = norm(key)
    for existing in row.keys():
        if norm(existing) == target:
            val = row.get(existing)
            return val if val else "—"
    alt_map = {
        "LifeStage": ["Life Stage", "life_stage"],
        "ProtectionLevel": ["Protection Level", "protection_level"],
        "MonthlyBudget": ["Monthly Budget", "monthly_budget"],
        "Whatsapp": ["Whatsapp", "WhatsApp", "wa_link", "WhatsApp Link"],
        "Name": ["name"],
        "Income": ["income"],
        "Phone": ["phone"],
        "Dependents": ["dependents"],
        "Email": ["email", "Email Address"],
        "Age": ["age"]
    }
    for k, alts in alt_map.items():
        if norm(key) == norm(k):
            for a in alts:
                for existing in row.keys():
                    if norm(existing) == norm(a):
                        val = row.get(existing)
                        return val if val else "—"
    return "—"

# -------------------------------------------------
# Helper for modern table rows
# -------------------------------------------------
def row_item(label, value):
    return f"""
    <tr>
        <td style="
            padding:12px 10px;
            color:#6b7280;
            border-bottom:1px solid #e5e7eb;
            width:45%;
        ">
            {label}
        </td>
        <td style="
            padding:12px 10px;
            font-weight:600;
            border-bottom:1px solid #e5e7eb;
            color:#111827;
        ">
            {value}
        </td>
    </tr>
    """

# -------------------------------------------------
# BUILD EMAIL HTML (Modern UI)
# -------------------------------------------------
def build_email_html(row):
    # Fixed WhatsApp number
    whatsapp_number = "+60168357258"
    whatsapp_link = f"https://wa.me/{whatsapp_number.lstrip('+')}"

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

<body style="
    margin:0;
    padding:0;
    background:#f4f6fb;
    font-family:'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color:#1f2937;
">

<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td align="center" style="padding:40px 15px;">

    <!-- Card -->
    <table width="100%" style="
        max-width:600px;
        background:#ffffff;
        border-radius:16px;
        box-shadow:0 10px 30px rgba(0,0,0,0.08);
        overflow:hidden;
    ">

        <!-- Header -->
        <tr>
        <td style="
            background:linear-gradient(135deg,#2563eb,#1e40af);
            padding:28px 30px;
            color:#ffffff;
        ">
            <h1 style="
                margin:0;
                font-size:22px;
                font-weight:600;
            ">
                Your Income Protection Summary
            </h1>
            <p style="
                margin:6px 0 0;
                opacity:0.9;
                font-size:14px;
            ">
                Satu Gaji Satu Harapan
            </p>
        </td>
        </tr>

        <!-- Body -->
        <tr>
        <td style="padding:30px;">

            <p style="font-size:16px;margin-top:0;">
                Hi <b>{v(row,'Name')}</b> 👋
            </p>

            <p style="color:#4b5563;">
                Thank you for completing your personalised income protection review.
                Here’s a clear summary prepared just for you:
            </p>

            <!-- Info Table -->
            <table width="100%" cellpadding="0" cellspacing="0" style="
                margin:25px 0;
                border-collapse:collapse;
                font-size:14px;
            ">

                {row_item("Age", v(row,'Age'))}
                {row_item("Life Stage", v(row,'LifeStage'))}
                {row_item("Dependents", v(row,'Dependents'))}
                {row_item("Protection Level", v(row,'ProtectionLevel'))}
                {row_item("Monthly Budget", v(row,'MonthlyBudget'))}
                {row_item("Annual Income", v(row,'Income'))}
                {row_item("Phone", v(row,'Phone'))}

            </table>

            <!-- CTA -->
            <div style="
                background:#f1f5f9;
                padding:18px;
                border-radius:12px;
                text-align:center;
                margin-top:30px;
            ">
                <p style="margin:0 0 10px;font-size:15px;">
                    Our licensed advisor will reach out to you shortly.
                </p>

                <a href="{whatsapp_link}" style="
                    display:inline-block;
                    padding:12px 22px;
                    background:#22c55e;
                    color:#ffffff;
                    text-decoration:none;
                    font-weight:600;
                    border-radius:999px;
                    font-size:14px;
                ">
                    💬 Chat on WhatsApp
                </a>
            </div>

        </td>
        </tr>

        <!-- Footer -->
        <tr>
        <td style="
            padding:22px 30px;
            background:#f9fafb;
            border-top:1px solid #e5e7eb;
            font-size:12px;
            color:#6b7280;
        ">
            <p style="margin:0 0 10px;">
                Subject to policy terms and final approval by authorised representatives.
            </p>

            <p style="margin:0;">
                Warm regards,<br>
                <b>{SENDER_NAME}</b>
            </p>
        </td>
        </tr>

    </table>

</td>
</tr>
</table>

</body>
</html>
"""

# -------------------------------------------------
# SEND EMAIL (UTF-8 safe, with PDF attachment)
# -------------------------------------------------
def send_email(to_email, subject, html_content, attachment_path="Benefits.pdf"):
    msg = MIMEMultipart("mixed")  # use mixed to allow attachments
    msg["From"] = f"{SENDER_NAME} <{SMTP_USERNAME}>"
    msg["To"] = to_email
    msg["Subject"] = Header(subject, 'utf-8')  # UTF-8 subject

    # HTML body in UTF-8
    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(html_part)

    # Attach PDF if exists
    if attachment_path and os.path.isfile(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(attachment_path)}"',
            )
            msg.attach(part)
    else:
        print(f"[Warning] Attachment not found: {attachment_path}")

    # Send email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

    print(f"[Email] Sent → {to_email} (with attachment: {os.path.basename(attachment_path)})")

# -------------------------------------------------
# UPDATE EmailSent COLUMN
# -------------------------------------------------
def update_email_sent(sheet, row_index):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    possible_headers = ["EmailSent", "Email_sent", "Email Sent", "EmailSentTimestamp", "Email_sent_timestamp"]
    headers = sheet.row_values(1)
    email_sent_col = None
    def norm(s): return str(s).lower().replace(" ", "").replace("_", "")
    for i, h in enumerate(headers, start=1):
        if norm(h) in [norm(x) for x in possible_headers]:
            email_sent_col = i
            break
    if not email_sent_col:
        email_sent_col = len(headers) + 1
        sheet.update_cell(1, email_sent_col, "Email_sent")
    sheet.update_cell(row_index, email_sent_col, timestamp)

# -------------------------------------------------
# MAIN PROCESS
# -------------------------------------------------
def process_pending_emails():
    sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
    rows = sheet.get_all_records()

    for idx, row in enumerate(rows, start=2):  # Row 2 = first data row
        email = v(row, "Email").strip()
        email_sent = v(row, "EmailSent").strip()

        if not email or email_sent:
            continue

        try:
            html = build_email_html(row)
            subject = "Your Personalised Income Protection Summary"

            send_email(email, subject, html)  # PDF included by default
            update_email_sent(sheet, idx)

        except Exception as e:
            print(f"[Error] Email failed → {email}: {e}")

# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    process_pending_emails()
