from flask import Flask, render_template, request, send_from_directory, session
import os
import logging
import random
import telebot
from scraper import scrape_data, notify_user  # ✅ Import notify_user

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session storage

logging.basicConfig(filename="scraper.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s", encoding="utf-8")

# Ensure output directory exists
OUTPUT_DIR = "output"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Telegram Bot Configuration
BOT_TOKEN = "your_telegram_bot_token"
CHAT_ID = "your_telegram_id"  # Change this to the admin's Telegram ID
bot = telebot.TeleBot(BOT_TOKEN)

# Function to send verification code via Telegram
def send_telegram_verification(user_telegram_id):
    verification_code = random.randint(100000, 999999)  # Generate a 6-digit code
    session["verification_code"] = verification_code  # Store in session for later verification
    bot.send_message(user_telegram_id, f"Your verification code: {verification_code}")
    return verification_code

# Route to send verification code to Telegram
@app.route("/verify_telegram", methods=["POST"])
def verify_telegram():
    user_telegram_id = request.form.get("telegram_id")
    if not user_telegram_id:
        return "Please enter your Telegram ID!", 400
    
    send_telegram_verification(user_telegram_id)
    return "Verification code sent to your Telegram!", 200

# Route to confirm verification code
@app.route("/confirm_code", methods=["POST"])
def confirm_code():
    user_code = request.form.get("verification_code")

    if int(user_code) == session.get("verification_code"):
        return "Verification successful!", 200
    else:
        return "Invalid code. Try again.", 400

# Route to handle CSV downloads
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

# Main scraping route
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form["url"]
        admin_email = "your_admin_email"  # Change this to the admin's email address
        client_ip = request.remote_addr  # Get the IP address of the client machine

        if not url:
            return render_template("index.html", error="Please enter a URL.")
        
        try:
            tables_data = scrape_data(url)  # Get table names, data, and filenames
            # Include the client IP in the email subject
            notify_user(admin_email, scrape_status="success", client_ip=client_ip)  # Notify user with IP
            bot.send_message(CHAT_ID, f"New scraping request from {client_ip}. Data retrieved successfully!")  # ✅ Notify admin on Telegram
            return render_template("index.html", success="Scraping completed successfully!", tables=tables_data)
        except Exception as e:
            logging.error(f"Scraping failed: {str(e)}")
            log_file = "scraper.log"
            notify_user(admin_email, scrape_status="error", log_file=log_file, client_ip=client_ip)  # Send log file and IP
            bot.send_message(CHAT_ID, f"Scraping failed from {client_ip}. Check log file.")  # ✅ Notify admin of failure
            
            return render_template("index.html", error=f"An error occurred: {str(e)}")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
