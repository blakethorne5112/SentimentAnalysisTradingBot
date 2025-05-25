import os
from dotenv import load_dotenv
import praw
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from sentiment_predictor import SentimentAnalyser

# Initialize sentiment analyzer
analyser = SentimentAnalyser()

class InvalidNoteError(ValueError):
    pass

load_dotenv()
API_KEY=os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID=os.getenv("GOOGLE_SEARCH_ENGINE_ID")

currentDate = datetime.now(ZoneInfo("America/New_York")).strftime("%Y/%m/%d")

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

def search_subreddit(subreddit_name, keyword, limit=10):
    subreddit = reddit.subreddit(subreddit_name)
    sentiment_counter = 5

    search_results = subreddit.search(keyword, sort="new", limit=50)
    sorted_posts = sorted(search_results, key=lambda post: post.score, reverse=True)[:limit]
    print(f"\nHere are the top 10 Reddit posts for keyword '{keyword}' on Reddit in the r/{subreddit_name} :\n")
    
    if not sorted_posts:
        print("No posts found. Try a different keyword or subreddit.")
        return

    for i, post in enumerate(sorted_posts, 1):
        try:
            # Get sentiment
            sentiment = analyser.predict(post.title)
            confidence = sentiment['probabilities'][sentiment['label']]
            if sentiment['sentiment'] == 'positive':
                sentiment_counter += (1 * confidence / 2)
            elif sentiment['sentiment'] == 'negative':
                sentiment_counter -= (1 * confidence / 2)
            print(f"{i}. {post.title}")
            print(f"   Upvotes: {post.score} | Sentiment: {sentiment['sentiment']} (Confidence: {confidence:.2f})\n")
        except Exception as e:
            print(f"Error processing post: {e}")
    overall_sentiment(sentiment_counter, keyword, "Reddit")

def overall_sentiment(sentiment_counter: float, keyword, platform) -> str:
    sentiment_string = ""
    if sentiment_counter >= 8:
        sentiment_string = "overwhelmingly positive"
    elif 6 < sentiment_counter < 8:
        sentiment_string = "positive"
    elif 4 <= sentiment_counter <= 6:
        sentiment_string = "mixed or neutral"
    elif 2 < sentiment_counter < 4:
        sentiment_string = "negative"
    elif sentiment_counter <= 2:
        sentiment_string = "overwhelmingly negative"
    print(f"Overall sentiment for '{keyword}' on {platform} is {sentiment_string} with a score of {sentiment_counter:.2f} / 10\n")

def google_custom_search(query: str, api_key: str, search_engine_id: str, sites: list[str]) -> dict:
    if not query or not query.strip():
        raise InvalidNoteError("Query must be a non‑empty string")
    
    site_filters = " OR ".join(f"site:{s}" for s in sites)
    full_query = f"{query} {site_filters}"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": full_query
    }
    
    response = requests.get(url, params=params)
    
    if not response.ok:
        raise Exception(f"Error: {response.status_code} – {response.reason}")
    
    return response.json()

def print_top_headlines(keyword, results: dict, max_results: int = 10) -> None:
    sentiment_counter = 5
    items = results.get("items", [])
    if not items:
        print("No results found.")
        return

    top_items = items[:max_results]
    print(f"Here are the top 10 News articles for {keyword} on Google :\n")

    for i, item in enumerate(top_items, start=1):
        title   = item.get("title", "").strip()
        raw_snippet = item.get("snippet", "").strip()
        snippet = raw_snippet.split("... ", 1)[-1].strip()
        link = item.get("link", "").strip()
        sentiment = analyser.predict(f"{title} {snippet}")
        confidence = sentiment['probabilities'][sentiment['label']]
        
        if sentiment['sentiment'] == 'positive':
            sentiment_counter += (1 * confidence / 2)
        elif sentiment['sentiment'] == 'negative':
            sentiment_counter -= (1 * confidence / 2)
        
        print(f"{i}. {title} - {link}")
        print(f"   Snippet: {snippet}")
        print(f"   Sentiment: {sentiment['sentiment']} (Confidence: {sentiment['probabilities'][sentiment['label']]:.2f})\n")
    overall_sentiment(sentiment_counter, keyword, "Google")

if __name__ == "__main__":
    stock_name = input("Enter the stock name: ").strip()
    try:
        search_subreddit("stocks", stock_name)
        domains = [
            "finance.yahoo.com/news", 
            "www.bloomberg.com/news", 
            "www.bbc.com/news", 
            f"www.cnbc.com/{currentDate}", 
            "www.investors.com/news", 
            "www.reuters.com/business", 
            "www.seekingalpha.com/news", 
            "www.marketwatch.com/story", 
            "www.investing.com/news"
        ]
        results = google_custom_search(f"{stock_name} news", API_KEY, SEARCH_ENGINE_ID, domains)
        print_top_headlines(stock_name, results, max_results=10)
    except Exception as e:
        print(f"Fatal error: {e}")