import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import logging
import re
from dotenv import load_dotenv
from urllib.parse import urlparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Load environment variables
load_dotenv()

# Configure output and log directories
OUTPUT_DIR = "output/"
LOG_DIR = "logs/"

# Telegram Bot Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(filename=os.path.join(LOG_DIR, "scraping_log.txt"), level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s", encoding="utf-8")


def clean_filename(name):
    """Remove invalid characters from filenames"""
    return re.sub(r'[\\/*?:"<>|]', '', name).replace(' ', '_')


def scrape_data(url):
    """Scrape table data from a given URL and save it as CSV"""
    parsed_url = urlparse(url)
    page_name = parsed_url.path.split('/')[-1] or "scraped_data"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    tables = soup.find_all('table')
    if not tables:
        raise ValueError(f"No tables found on {url}")

    all_tables_data = []

    for i, table in enumerate(tables):
        try:
            heading = table.find_previous(['h2', 'h3'])  # Find nearest heading
            table_name = clean_filename(heading.text.strip()) if heading else f"Table {i+1}"

            # Extract headers
            headers = [header.text.strip() for header in table.find('tr').find_all(['th', 'td'])] if table.find('tr') else []
            df = pd.DataFrame(columns=headers)

            # Extract rows
            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                row_data = [cell.text.strip() for cell in row.find_all('td')]
                if row_data and len(row_data) == len(headers):
                    df.loc[len(df)] = row_data

            if df.empty:
                logging.warning(f"Skipping Table {i+1}: No data rows")
                continue

            # Save CSV
            csv_filename = f"{page_name}_{table_name}.csv"
            csv_filepath = os.path.join(OUTPUT_DIR, csv_filename)
            df.to_csv(csv_filepath, index=False, mode='w', header=True)
            logging.info(f"Table {i+1} ({table_name}) saved to {csv_filename}")

            all_tables_data.append({
                "name": table_name,
                "data": df.to_html(classes="table table-striped", index=False),
                "filename": csv_filename
            })

        except Exception as e:
            logging.error(f"Error processing table {i+1}: {str(e)}")
            raise

    return all_tables_data


def send_email(subject, body, to_email, attachment=None):
    """Send an email with an optional attachment"""
    from_email = os.getenv('GMAIL_USER')
    password = os.getenv('GMAIL_PASSWORD')

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if attachment:
        try:
            with open(attachment, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment)}")
                msg.attach(part)
        except Exception as e:
            logging.error(f"Failed to attach file: {e}")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Email sending failed: {e}")


def send_telegram_message(message):
    """Send a message to the admin via Telegram bot"""
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logging.info("Telegram message sent successfully!")
        except requests.exceptions.RequestException as e:
            logging.error(f"Telegram notification failed: {e}")


def notify_user(user_email, scrape_status, log_file=None, client_ip=None):
    """Send notifications via Email & Telegram when a user scrapes data"""
    subject = f"Web Scraping Status from {client_ip}"
    body = f"Status: {scrape_status.upper()}\nIP: {client_ip}"

    if scrape_status == "success":
        body += "\nScraping completed successfully!"
    else:
        body += "\n⚠️ Scraping failed. Check the logs."

    # ✅ Send Email
    if log_file:
        send_email(subject, body, user_email, log_file)
    else:
        send_email(subject, body, user_email)

    # ✅ Send Telegram Alert
    send_telegram_message(f"📢 Web Scraping Alert!\n\n{body}")


def log_scrape():
    """Retrieve the log file contents"""
    log_file = os.path.join(LOG_DIR, "scraping_log.txt")
    with open(log_file, "r") as f:
        return f.read()
