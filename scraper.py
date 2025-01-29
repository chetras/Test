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
import os

# Configure output folder
OUTPUT_DIR = "output/"
LOG_DIR = "logs/"
load_dotenv()

def clean_filename(name):
    """Remove invalid characters from filenames"""
    return re.sub(r'[\\/*?:"<>|]', '', name).replace(' ', '_')

def scrape_data(url):
    parsed_url = urlparse(url)
    page_name = parsed_url.path.split('/')[-1] or "scraped_data"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    tables = soup.find_all('table')
    if not tables:
        raise ValueError(f"No tables found on {url}")

    all_tables_data = []  # Store table names, data, and filenames for rendering

    for i, table in enumerate(tables):
        try:
            heading = table.find_previous(['h2', 'h3'])  # Find nearest heading
            table_name = clean_filename(heading.text.strip()) if heading else f"Table {i+1}"

            # Handle headers
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [header.text.strip() for header in header_row.find_all(['th', 'td'])]

            df = pd.DataFrame(columns=headers)
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

    return all_tables_data  # Return list of tables with names and filenames


def log_scrape():
    log_file = os.path.join(LOG_DIR, "scraping_log.txt")
    with open(log_file, "r") as f:
        return f.read()  # Read the log data to send in email or display
def send_email(subject, body, to_email, attachment=None):
    from_email = os.getenv('GMAIL_USER')
    password = os.getenv('GMAIL_PASSWORD')

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment:
        try:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(attachment, 'rb').read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment)}')
            msg.attach(part)
        except Exception as e:
            print(f"Failed to attach file: {e}")

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("Email Sent Successfully!")
    except Exception as e:
        print(f"Email Sending Failed: {e}")

# Call this function after scraping is done
def notify_user(user_email, scrape_status, log_file=None):
    if scrape_status == "success":
        subject = "A User Has Completed Web Scraping Successfully!"
        body = f"A user has successfully completed the web scraping process. The scraped data is available for download. Here are the details:\n\nUser Email: {user_email}\n\nYou can download the scraped data here: <download_link>"
        send_email(subject, body, user_email)  # No log file to send
    else:
        subject = "Error in User's Web Scraping Process!"
        body = f"An error occurred while a user was attempting to scrape data. Please check the attached log file for more information.\n\nUser Email: {user_email}"
        if log_file:
            send_email(subject, body, user_email, log_file)  # Send the log file if there's an error
        else:
            send_email(subject, body, user_email)  # Send email without the log file if not available

