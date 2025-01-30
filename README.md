Web Scrapiing Automation Project 

Overview

This project automates the process of web scraping, extracting valuable data from websites, storing it securely, and notifying administrators in real time through various channels like email and Telegram. The goal is to gather table data from multiple websites and store it efficiently in CSV files, while ensuring security and ease of use

Features
- Automated Web Scraping: Scrape table data from websites on a scheduled basis.
- Data Storage: Store scraped data securely in CSV files.
- Real-time Notifications: Notify administrators through Telegram or email upon successful scraping or failure.
- Error Handling: Gracefully handle errors during scraping and provide logging for troubleshooting.
- Security Measures: Protect sensitive data and ensure secure communications.

Installation 
1. Clone the repository
   git clone https://github.com/your-username/web-scraping-automation.git
2. Install the required dependencies
   pip install -r requirements.txt
3. Set up your environment variables:
-    Telegram Bot API Token (for notifications)
-    Email configurations (SMTP settings)

Configuration
- You need to edit the .env file to your specific use case
GMAIL_USER="your_gmail_user_address"
GMAIL_PASSWORD="your_gmail_password"
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
TELEGRAM_CHAT_ID="your_telegram_chat_id"

- Some of the code there you need to hardcode you value above so if you can modify that thank you
