# SatuGajiSatuHarapan.py
# Web server for the "Protecting My Income" chatbot using Flask
# Integrated with Google Sheets (Campaign1) to save session data automatically

from flask import Flask, request, jsonify, render_template, session
from datetime import datetime
import re
from googlesheet import save_session  

class SGSHChatbot:
    def __init__(self):
        self.state = "start"
        self.user_data = {}

    # -------------------------
    # Helper: calculate age
    # -------------------------
    def calculate_age(self, dob_str):
        try:
            dob = datetime.strptime(dob_str, "%d/%m/%Y")
            today = datetime.today()
            age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )
            return age
        except ValueError:
            return None

    # -------------------------
    # Helper: parse income
    # -------------------------
    def parse_income(self, message):
        cleaned = re.sub(r"[^\d]", "", message)
        return int(cleaned) if cleaned.isdigit() else None

    # -------------------------
    # Helper: validate email
    # -------------------------
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    # -------------------------
    # Helper: validate Malaysian phone
    # -------------------------
    def validate_malaysian_phone(self, phone):
        phone = re.sub(r"[^\d]", "", phone)  # remove non-digits
        # Valid formats: starts with 60 (country code) or 01
        return bool(re.match(r"^(60\d{8,9}|01\d{7,8})$", phone))

    # -------------------------
    # Main chatbot logic
    # -------------------------
    def process(self, message):
        message = message.strip()

        # Allow reset anytime
        if message.lower() == "menu":
            self.__init__()
            return "Returning to main menu. Please choose an option."

        # --- Step 1: Greet and ask name ---
        if self.state == "start":
            self.state = "ask_name"
            return "Hello! I'm Erica, your super agent that will guide you today 😊\nMay I know your name?"

        # --- Step 2: Ask for name ---
        if self.state == "ask_name":
            if not message:
                return "Please enter your name to continue."
            self.user_data["name"] = message
            self.state = "ask_dob"
            return (
                f"Hello, {message}! Nice to meet you! Let’s get to know you better. 😊\n"
                f"May I know your Date of Birth?\n(Format: DD / MM / YYYY )"
            )

        # --- Step 3: Ask for DOB ---
        if self.state == "ask_dob":
            if not message:
                return "You did not enter anything.\nPlease enter your Date of Birth (DD/MM/YYYY)."

            age = self.calculate_age(message)
            if age is None:
                return (
                    "Invalid date format, please try again ❌\n"
                    "Please enter your Date of Birth as DD/MM/YYYY\n"
                    "Example: 25/12/1990"
                )

            self.user_data["dob"] = message
            self.user_data["age"] = age
            self.state = "ask_life_stage"
            return (
                f"Great! You are {age} years old.\n It is the perfect age to start building a strong foundation for your future savings"
                f"May I know what is your current life stage?\n"
                f"1. Just married\n"
                f"2. I have a young child / Children\n"
                f"3. Nearing Retirement \n"
                f"4. Single and independent"
            )

        # --- Step 4: Ask for life stage ---
        if self.state == "ask_life_stage":
            options = {
                "1": "Just married",
                "2": "I have a young child / Children",
                "3": "Nearing Retirement",
                "4": "Single and independent"
            }
            if message not in options:
                return (
                    "Please choose a valid option: 1, 2, 3, or 4.\n"
                    f"What is your current life stage?\n"
                    f"1. Just married\n"
                    f"2. I have a young child / Children\n"
                    f"3. Nearing Retirement\n"
                    f"4. Single and independent"
                )
            self.user_data["life_stage"] = options[message]
            self.state = "ask_dependents"
            return (
                f"Thank you! Your life stage is: {options[message]}\n"
                f"How many dependents do you have?\n"
                f"1. 1 only\n"
                f"2. 1-2 person\n"
                f"3. 3-4 person\n"
                f"4. More than 4 person"
            )

        # --- Step 5: Ask for dependents ---
        if self.state == "ask_dependents":
            options = {
                "1": "1 only",
                "2": "1-2 person",
                "3": "3-4 person",
                "4": "More than 4 person"
            }
            if message not in options:
                return (
                    "Please choose a valid option: 1, 2, 3, or 4.\n"
                    f"How many dependents do you have?\n"
                    f"1. 1 only\n"
                    f"2. 1-2 person\n"
                    f"3. 3-4 person\n"
                    f"4. More than 4 person"
                )
            self.user_data["dependents"] = options[message]
            self.state = "ask_protection_level"
            return (
                f"Thank you! You have {options[message]} dependents.\n"
                f"What is your current level of protection?\n"
                f"1. No coverage at all\n"
                f"2. Basic employee coverage\n"
                f"3. Some personal coverage\n"
                f"4. Comprehensive coverage"
            )

        # --- Step 6: Ask for protection level ---
        if self.state == "ask_protection_level":
            options = {
                "1": "No coverage at all",
                "2": "Basic employee coverage",
                "3": "Some personal coverage",
                "4": "Comprehensive coverage"
            }
            if message not in options:
                return (
                    "Please choose a valid option: 1, 2, 3, or 4.\n"
                    f"What is your current level of protection?\n"
                    f"1. No coverage at all\n"
                    f"2. Basic employee coverage\n"
                    f"3. Some personal coverage\n"
                    f"4. Comprehensive coverage"
                )
            self.user_data["protection_level"] = options[message]
            self.state = "ask_budget"
            return (
                f"Thank you! Your protection level is: {options[message]}\n"
                f"May I know your budget for monthly premium?\n"
                f"1. Less than RM200\n"
                f"2. RM201 - RM500\n"
                f"3. RM501 - RM1000\n"
                f"4. More than RM1000"
            )

        # --- Step 7: Ask for budget ---
        if self.state == "ask_budget":
            options = {
                "1": "Less than RM200",
                "2": "RM201 - RM500",
                "3": "RM501 - RM1000",
                "4": "More than RM1000"
            }
            if message not in options:
                return (
                    "Please choose a valid option: 1, 2, 3, or 4.\n"
                    f"May I know your budget for monthly premium?\n"
                    f"1. Less than RM200\n"
                    f"2. RM201 - RM500\n"
                    f"3. RM501 - RM1000\n"
                    f"4. More than RM1000"
                )
            self.user_data["budget"] = options[message]
            self.state = "ask_phone"  # NEW STEP
            return (
                f"Thank you! Your monthly budget is: {options[message]}\n"
                "Please enter your phone number so we can provide you with updates from time to time on suitable offers and packages."
            )

        # --- Step 7b: Ask for phone number ---
        if self.state == "ask_phone":
            if not self.validate_malaysian_phone(message):
                return (
                    "Please enter a valid Malaysian phone number.\n"
                    "Examples: 0123456789 or 60123456789"
                )
            self.user_data["phone"] = message
            self.state = "ask_income"
            return (
                f"Thank you! Your phone number is: {message}\n"
                "May I know your annual income?\n"
                "(Example: RM 30,000)"
            )

        # --- Step 8: Ask for income ---
        if self.state == "ask_income":
            income = self.parse_income(message)
            if income is None or income <= 0:
                return (
                    "Please enter a valid income amount.\n"
                    "Example: RM 30000 or 30,000"
                )

            self.user_data["income"] = income

            # --- Calculations ---
            age = self.user_data["age"]
            years_coverage = max(60 - age, 0)
            recommended_coverage = max(income * 10, 300000)

            if age <= 30:
                rate = 6
            elif age <= 40:
                rate = 8
            elif age <= 50:
                rate = 10
            else:
                rate = 12

            annual_premium = (recommended_coverage / 1000) * rate
            monthly_premium = annual_premium / 12

            self.state = "ask_email"

            return (
                f"Thank you, {self.user_data['name']}! 😊 We really appreciate you taking the time to share a bit about yourself.\n"
                f"Based on what you’ve told us, here’s a personalised quote created just for you.\n\n"
                f"📝 *Your Personalised Income Protection Plan* 📝\n"
                f"{'-' * 38}\n"
                f"{'Years of Coverage:':25} {years_coverage} years\n"
                f"{'Recommended Coverage:':25} RM {recommended_coverage:,.2f}\n"
                f"{'Premium Rate:':25} RM {rate} per RM1,000\n"
                f"{'Annual Premium:':25} RM {annual_premium:,.2f}\n"
                f"{'Monthly Premium:':25} RM {monthly_premium:,.2f}\n"
                f"{'-' * 38}\n\n"
                "Please type your email address, we will send you an email summary of our conversation for your reference"
            )

        # --- Step 9: Ask for email ---
        if self.state == "ask_email":
            if not self.validate_email(message):
                return "Please enter a valid email address.\nExample: example@email.com"

            self.user_data["email"] = message
            # Save to Google Sheets immediately (this will auto-send an email)
            save_session(self.user_data)

            self.state = "ask_more_info"
            return (
                "Thank you! Your email is saved and we will send you a summary via email shortly.\n"
                "Would you like to find out more on how you can be best protected?\n"
                "1. Yes\n"
                "2. No"
            )

        # --- Step 10: Ask if user wants more info ---
        if self.state == "ask_more_info":
            options = {"1": "Yes", "2": "No"}
            if message not in options:
                return (
                    "Please choose a valid option: 1 or 2.\n"
                    "Would you like to find out more on how you can be best protected?\n"
                    "1. Yes\n"
                    "2. No"
                )
            self.user_data["more_info"] = options[message]
            self.state = "done"

            # --- Final messages split into 2 chat bubbles ---
            final_messages = [
                "Great! Thank you for signing up. We will contact you soon 😊\n"
                "Subject to terms and conditions of approved policy after recommendation by authorised representatives.",
                
                "Thank you for contacting us. Feel free to reach out to us if you would like more information at https://wa.me/60168357258"
            ]
            return "\n\n".join(final_messages)

        # --- Done ---
        if self.state == "done":
            return "If you want to calculate again, type *restart*."

        return "I'm not sure what you mean. Please try again."


# -------------------------
# Flask app setup
# -------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/')
def Chatbot():
    return render_template('Chatbot.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    message = data.get('message', '')
    tab_id = data.get('tab_id', 'default')

    states = session.get('chatbot_states', None)
    if states is None and 'chatbot' in session:
        states = {'default': session.pop('chatbot')}
    if states is None:
        states = {}

    if tab_id not in states:
        states[tab_id] = SGSHChatbot().__dict__

    chatbot = SGSHChatbot()
    chatbot.__dict__.update(states[tab_id])

    reply = chatbot.process(message)

    states[tab_id] = chatbot.__dict__
    session['chatbot_states'] = states
    session.modified = True

    return jsonify({'reply': reply})

@app.route('/reset', methods=['POST'])
def reset_chat():
    data = request.get_json(silent=True) or {}
    tab_id = data.get('tab_id', 'default')

    states = session.get('chatbot_states', {})
    if not states and 'chatbot' in session:
        states = {'default': session.pop('chatbot')}

    if tab_id in states:
        states.pop(tab_id, None)
        session['chatbot_states'] = states
        session.modified = True

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True)
