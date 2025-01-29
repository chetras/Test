from flask import Flask, render_template, request, send_from_directory
import os
import logging
from scraper import scrape_data, notify_user  # ✅ Import notify_user
app = Flask(__name__)

logging.basicConfig(filename="scraper.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s", encoding="utf-8")

# Ensure output directory exists
OUTPUT_DIR = "output"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Route to handle CSV downloads
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form["url"]
        admin_email = "chetraso721@gmail.com"
        if not url:
            return render_template("index.html", error="Please enter a URL.")
        try:
            tables_data = scrape_data(url)  # Get table names, data, and filenames
            notify_user(admin_email, scrape_status="success")  # ✅ Notify user on success
            return render_template("index.html", success="Scraping completed successfully!", tables=tables_data)
        except Exception as e:
            logging.error(f"Scraping failed: {str(e)}")
            
            # Send the scraper.log file to admin on failure
            log_file = "scraper.log"
            notify_user(admin_email, scrape_status="error", log_file=log_file)  # Send log file with error notification
            
            return render_template("index.html", error=f"An error occurred: {str(e)}")
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
