import os
from dotenv import load_dotenv
import praw
from sentiment_predictor import SentimentAnalyser

# Initialize sentiment analyzer
analyser = SentimentAnalyser()

load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

def search_subreddit(subreddit_name, keyword, limit=10):
    subreddit = reddit.subreddit(subreddit_name)
    
    # Search for posts
    search_results = subreddit.search(keyword, sort="new", limit=50)
    
    # Convert generator to list and sort by upvotes
    sorted_posts = sorted(search_results, key=lambda post: post.score, reverse=True)[:limit]
    
    # Debug: Print number of posts found
    print(f"Found {len(sorted_posts)} posts for keyword '{keyword}' in r/{subreddit_name}.")
    
    if not sorted_posts:
        print("No posts found. Try a different keyword or subreddit.")
        return

    # Process posts
    for idx, post in enumerate(sorted_posts, 1):
        try:
            # Get sentiment
            sentiment = analyser.predict(post.title)
            print(f"{idx}. {post.title}")
            print(f"   Upvotes: {post.score} | Sentiment: {sentiment['sentiment']} (Confidence: {sentiment['probabilities'][sentiment['label']]:.2f})\n")
        except Exception as e:
            print(f"Error processing post: {e}")

if __name__ == "__main__":
    stock_name = input("Enter the stock name: ").strip()
    try:
        search_subreddit("stocks", stock_name)
    except Exception as e:
        print(f"Fatal error: {e}")