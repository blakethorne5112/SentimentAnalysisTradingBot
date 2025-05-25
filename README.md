# Sentiment Analysis Trading Bot

A Python-based educational application that uses sentiment analysis of Reddit posts to attempt to predict the direction of the market. The bot scrapes financial discussions from the internet, analyses the sentiment of posts, and executes trades based on the sentiment trends.

## Features

- **Reddit and Google Sentiment Analysis**: Scrapes and analyses sentiment from r/stocks as well as many popular financial news sources on Google
- **Practice Trading System**: Practice trading on the current day or past dates, choosing a particular company with the option to trade based on previously collected sentiment data
- **Market Calendar Integration**: Respects market hours and trading schedules
- **Automatic Sentiment Analysis Script**: Runs automatically on a predefined schedule (9 AM ET) to collect sentiment data for the day
- **Stock Data Integration**: Fetches real-time stock prices and market data
- **Comprehensive Logging**: Tracks all activities and decisions

## Project Structure

```
SentimentAnalysisTradingBot/
├── sentiment_analysis/
    ├── trade_executor.py      # Practice trading script (Main script)
    ├── reddit_scraper.py      # Social media data sentiment data collection
    └── automatic_sentiment.py # Automated sentiment collection script
└── README.md                  # This file
```

## Prerequisites

- Python 3.9 or higher
- Pip installed
- Reddit API credentials (PRAW) (Setup shown further down)
- Google Custom Search credentials (Setup shown further down)

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/blakethorne5112/SentimentAnalysisTradingBot.git
cd SentimentAnalysisTradingBot
```

### 2. ⚠️ **Important Step** ⚠️ Download the model and additional required files (too large for GitHub)
Available for download from this [Google Drive link](https://drive.google.com/file/d/13Tj1ypK4i3gh-WWfkO3tCRx6IwXL5EYG/view?usp=sharing).
* The program **WILL NOT** function without this additional download.

### 3. Unzip and merge
* Unzip the downloaded folder from Step 2
* Locate the 'SentimentAnalysisTradingBot' folder that was cloned in Step 1 in your computer's file directory
* Windows - Drag and drop the contents of the newly unzipped file into this folder
* Other OS - Google merging folders

### 4. Install required dependencies
```bash
pip install python-dotenv praw requests schedule pytz yfinance pandas pandas-market-calendars tabulate
```

Or install individually:
```bash
pip install python-dotenv
pip install praw
pip install requests
pip install schedule
pip install pytz
pip install yfinance
pip install pandas
pip install pandas-market-calendars
pip install tabulate
```

## Configuration

### Reddit API Setup
1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Create a new application (script type)
3. Note down your client ID and client secret
4. Add these credentials to your `.env` file

### Google Custom Search API Setup
1. Create a Google Cloud Project and Enable the API
  * Navigate to Google Cloud Console and sign in with your Google account
  * Click on the project dropdown at the top, click "New Project". Enter a project name (e.g., "Custom Search API Project") and then click "Create"
  * In the left sidebar, go to "APIs & Services" → "Library", search for "Custom Search API", click on "Custom Search API" from the results and then click "Enable"
2. Create API Credentials
  * Go to "APIs & Services" → "Credentials", click "Create Credentials" → "API Key", copy and save your API key (it will look like: AIzaSyB...)
3. Create a Custom Search Engine
  * Navigate to Google Custom Search Engine and sign in with the same Google account
  * Click "Add" or "Create a custom search engine" and fill in the required fields.
    * Sites to search: *
    * Language: English
    * Name of the search engine: Any
  * Click "Create", and you'll be taken to the control panel for your search engine
  * In the control panel, click "Setup" in the left sidebar. Look for "Search engine ID" - it will be a string like: "017576662512468239146:omuauf_lfve", copy and save this ID
4. Add the API Key and Search engine ID credentials to your `.env` file

## Usage

### Basic Usage

#### Run the main application:
```bash
cd sentiment_analysis
python trade_executor.py
```

#### Run the automatic sentiment script:
```bash
cd sentiment_analysis
python automatic_sentiment.py
```

#### Run the sentiment scraper manually and independently:
```bash
cd sentiment_analysis
python reddit_scraper.py
```

## How It Works

1. **Data Collection**: The bot scrapes financial discussions from Reddit using the PRAW library and financial articles from Google using the Google Custom Search Engine
2. **Sentiment Analysis**: Posts are analysed for sentiment using natural language processing
3. **Sentiment Score**: Sentiment trends are calculated into an overall sentiment score (score /10) and saved to a JSON file
5. **Practice Trading**: Real market data is pulled using the yfinance library, where you may choose to act based on sentiment data or otherwise test different trading strategies on past or current dates
6. **Monitoring**: All practice trading and sentiment analysis is logged for review and analysis, either in the console output or to a JSON file

## Scheduling

The automatic sentiment script can run on a schedule using the built-in scheduler. The script MUST be running the whole time for it to work.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Disclaimer

⚠️ **Important**: This program is for educational and research purposes. This program cannot trade with real money or connect to any trading platform and does not offer financial advice.

The developer is not responsible for any financial losses incurred from trading based on the data that this program produces.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/blakethorne5112/SentimentAnalysisTradingBot/issues) page
2. Create a new issue with detailed information
3. Provide logs and error messages when possible

## Acknowledgments

- Reddit API (PRAW) for data access
- Yahoo Finance (yfinance) for market data
- pandas and related libraries for data processing
- The open-source community for various utilities and tools
