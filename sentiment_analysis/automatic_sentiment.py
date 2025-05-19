import schedule
import time
import subprocess
import logging
from datetime import datetime
import pytz

# Set up logging
try:
    import logging.handlers
    log_handler = logging.handlers.RotatingFileHandler(
        "automatic_sentiment.log", 
        maxBytes=20*1024,  # 20KB per file
        backupCount=1 
    )
    console_handler = logging.StreamHandler()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[log_handler, console_handler]
    )
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("automatic_sentiment.log"),
            logging.StreamHandler()
        ]
    )

# List of Stock Tickers to get sentiment data on
STOCKS = [
    "TSLA", # Tesla, Tech, Controversial
    "NVDA", # Nvidia, Tech, Somewhat Controversial
    "AAPL", # Apple, Tech, Somewhat Controversial
    "PFE", # Pfizer, Healthcare, Non-controversial
    "GME", # GameStop, Retail, Controversial
    "LMT",  # Lockheed Martin, Defense, Non-controversial
    "^SPX", # S&P 500, Index, Non-controversial
    "SBUX", # Starbucks, Consumer Goods, Controversial
    "F", # Ford, Automotive, Non-controversial
    "CLF", # Cleveland-Cliffs, Mining, Non-controversial
]

# Target timezone
TIMEZONE = pytz.timezone("America/New_York")

def run_reddit_scraper(keyword):
    # Run the reddit_scraper.py script with the given stock
    try:
        logging.info(f"Starting sentiment analysis for stock: '{keyword}'")
        process = subprocess.Popen(
            ["python", "sentiment_analysis\\reddit_scraper.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Send the stock to the script's input prompt
        stdout, stderr = process.communicate(input=f"{keyword}\n")
        if process.returncode == 0:
            logging.info(f"Successfully processed stock: '{keyword}'")
            return True
        else:
            logging.error(f"Error processing stock '{keyword}'. Return code: {process.returncode}")
            logging.error(f"stderr: {stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Unexpected error processing stock '{keyword}': {str(e)}")
        return False

def daily():
    # Run sentiment analysis for all keywords in sequence
    current_time_ny = datetime.now(TIMEZONE)
    logging.info(f"Starting analysis at {current_time_ny.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    start_time = time.time()
    
    successful_keywords = 0
    failed_keywords = 0
    
    for stock in STOCKS:
        success = run_reddit_scraper(stock)
        if success:
            successful_keywords += 1
        else:
            failed_keywords += 1
        time.sleep(2)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logging.info(f"Process completed in {duration:.2f} seconds")
    logging.info(f"Successful stocks: {successful_keywords}, Failed stocks: {failed_keywords}")

def main():
    logging.info(f"Automatic Sentiment Analysis process started")
    logging.info(f"Scheduled to run daily at 9:00 AM with 10 stocks")
    schedule.every().day.at("09:00", TIMEZONE).do(daily)
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()