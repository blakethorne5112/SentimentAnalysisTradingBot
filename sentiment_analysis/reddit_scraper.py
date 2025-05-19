import os
from dotenv import load_dotenv
import json
import praw
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from sentiment_predictor import SentimentAnalyser
import trade_executor as TradeExecutor

# Initialize sentiment analyzer
analyser = SentimentAnalyser()

class InvalidNoteError(ValueError):
    pass

load_dotenv()
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID=os.getenv("GOOGLE_SEARCH_ENGINE_ID")
TWITTER_API_KEY=os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET=os.getenv("TWITTER_API_SECRET")
TWITTER_BEARER_TOKEN=os.getenv("TWITTER_BEARER_TOKEN")

currentDate = datetime.now(ZoneInfo("America/New_York")).strftime("%Y/%m/%d")
final_overall_sentiment = 0
number_of_working_apis = 0

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
    global final_overall_sentiment, number_of_working_apis
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
    final_overall_sentiment += sentiment_counter
    number_of_working_apis += 1
    print(f"Overall sentiment for '{keyword}' on {platform} is {sentiment_string} with a score of {sentiment_counter:.2f} / 10\n")

def google_custom_search(query: str, google_api_key: str, search_engine_id: str, sites: list[str]) -> dict:
    if not query or not query.strip():
        raise InvalidNoteError("Query must be a non‑empty string")
    
    site_filters = " OR ".join(f"site:{s}" for s in sites)
    full_query = f"{query} {site_filters}"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
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

def search_tweets(keyword, count=5, max_attempts=3):
    if not TWITTER_BEARER_TOKEN:
        print("Error: Bearer token not found. Please set TWITTER_BEARER_TOKEN environment variable.")
        return None
    
    headers = {
        'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'
    }
    url = 'https://api.twitter.com/2/tweets/search/recent'
    params = {
        'query': keyword,
        'max_results': min(10, count * 2),
        'tweet.fields': 'created_at,public_metrics,author_id,text',
        'expansions': 'author_id',
        'user.fields': 'name,username',
        'sort_order': 'relevancy'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 429:
            # Rate limit exceeded
            print(f"Twitter Rate limit exceeded. Thanks Elon!")
            return "ratelimit"
            
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            print(response.text)
            
            if "exceeded the monthly Tweet cap" in response.text:
                print("You've reached your monthly tweet cap for the free tier.")
                return None
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def format_tweets(tweet_data, count):
    if tweet_data == "ratelimit":
        print("Twitter API Rate limit exceeded. Cannot fetch tweets at this time.")
        return []
    if not tweet_data or 'data' not in tweet_data:
        print("No tweets found or API error occurred")
        return []
    
    tweets = tweet_data['data']
    users = {user['id']: user for user in tweet_data.get('includes', {}).get('users', [])}
    
    sorted_tweets = sorted(
        tweets, 
        key=lambda x: (
            x['public_metrics'].get('retweet_count', 0) + 
            x['public_metrics'].get('like_count', 0)
        ),
        reverse=True
    )
    
    top_tweets = sorted_tweets[:count]
    
    formatted_tweets = []
    for i, tweet in enumerate(top_tweets, 1):
        author = users.get(tweet['author_id'], {'name': 'Unknown', 'username': 'unknown'})
        created_at = datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
        
        metrics = tweet['public_metrics']
        popularity_score = metrics.get('retweet_count', 0) + metrics.get('like_count', 0)
        
        formatted_tweet = {
            'rank': i,
            'text': tweet['text'],
            'author_name': author['name'],
            'author_username': author['username'],
            'created_at': created_at,
            'retweets': metrics.get('retweet_count', 0),
            'likes': metrics.get('like_count', 0),
            'replies': metrics.get('reply_count', 0),
            'quotes': metrics.get('quote_count', 0),
            'popularity_score': popularity_score,
            'url': f"https://twitter.com/{author['username']}/status/{tweet['id']}"
        }
        
        formatted_tweets.append(formatted_tweet)
    
    return formatted_tweets

def display_tweets(formatted_tweets, keyword):
    if not formatted_tweets:
        return
    sentiment_counter = 5
    print(f"\nTop {len(formatted_tweets)} tweets about '{keyword}':\n")
    
    for tweet in formatted_tweets:
        sentiment = analyser.predict(f"{tweet['text']}")
        confidence = sentiment['probabilities'][sentiment['label']]

        if sentiment['sentiment'] == 'positive':
            sentiment_counter += (1 * confidence)
        elif sentiment['sentiment'] == 'negative':
            sentiment_counter -= (1 * confidence)
        print(f"{tweet['rank']}. {tweet['text']} - Score: {tweet['popularity_score']} (♻️ {tweet['retweets']} | ❤️ {tweet['likes']})")
        print(f"   By @{tweet['author_username']} ({tweet['author_name']}) on {tweet['created_at']}")
        print(f"   {tweet['url']}")
        print(f"Sentiment: {sentiment['sentiment']} (Confidence: {sentiment['probabilities'][sentiment['label']]:.2f})\n")
    overall_sentiment(sentiment_counter, keyword, "Twitter / X")

def final_sentiment():
    global final_overall_sentiment, number_of_working_apis
    if number_of_working_apis == 0:
        print("No working APIs found.")
        return
    
    overall_sentiment_score = final_overall_sentiment / number_of_working_apis
    sentiment_string = ""
    
    if overall_sentiment_score >= 8:
        sentiment_string = "overwhelmingly positive"
    elif 6 < overall_sentiment_score < 8:
        sentiment_string = "positive"
    elif 4 <= overall_sentiment_score <= 6:
        sentiment_string = "mixed or neutral"
    elif 2 < overall_sentiment_score < 4:
        sentiment_string = "negative"
    elif overall_sentiment_score <= 2:
        sentiment_string = "overwhelmingly negative"
    
    print(f"Overall sentiment for all platforms is {sentiment_string} with a score of {overall_sentiment_score:.2f} / 10\n")
    return overall_sentiment_score

def log_sentiment_to_json(stock_name: str, sentiment: float, log_path='sentiment_log.json') -> None:
    entry = {
        "stock_name": stock_name,
        "sentiment": f"{sentiment:.2f}",
        "date": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
    }
    try:
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        if "logs" not in data or not isinstance(data["logs"], list):
            data["logs"] = []
        data["logs"].append(entry)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Logged sentiment for {stock_name} on {entry['date']}")

    except Exception as e:
        print(f"Error logging sentiment: {e}")

def main():
    stock_name = input("Enter the stock name: ").strip()
    ticker = TradeExecutor.get_stock_from_user_input(stock_name)
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
        results = google_custom_search(f"{stock_name} news", GOOGLE_API_KEY, SEARCH_ENGINE_ID, domains)
        print_top_headlines(stock_name, results, max_results=10)
        # tweets = search_tweets(stock_name, count=5)
        # formatted_tweets = format_tweets(tweets, count=5)
        # display_tweets(formatted_tweets, stock_name)
        sentiment = round(final_sentiment(), 2)
        log_sentiment_to_json(ticker, sentiment)
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()