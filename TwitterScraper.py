from playwright.sync_api import sync_playwright
import json

def scrape_tweet(url: str) -> dict:
    """
    Scrape a single tweet page for Tweet thread
    Return parent tweet, reply tweets and recommended tweets
    """
    _xhr_calls = []

    def intercept_response(response):
        # intercept all background requests and save them
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # enable background request intercepting:
        page.on("response", intercept_response)
        page.goto(url)
        page.wait_for_selector("[data-testid='tweet']")

        # find all tweet background requests:
        tweet_calls = [f for f in _xhr_calls if "TweetResultByRestId" in f.url]
        for tc in tweet_calls:
            data = tc.json()
            tweet_data = data['data']['tweetResult']['result']

            # saving only the data that will be relevant for sentiment analysis
            extracted_data = {
                "user": {
                    "id": tweet_data.get("core", {}).get("user_results", {}).get("result", {}).get("rest_id"),
                },
                "text": tweet_data.get("legacy", {}).get("full_text"),
                "created_at": tweet_data.get("legacy", {}).get("created_at"),
                "like_count": tweet_data.get("legacy", {}).get("favorite_count"),
                "retweet_count": tweet_data.get("legacy", {}).get("retweet_count"),
                "reply_count": tweet_data.get("legacy", {}).get("reply_count"),
            }
            return extracted_data

def scrape_profile(url: str):
    """
    Scrape the information from a profile
    """
    _xhr_calls = []

    def intercept_response(response):
        # intercept all background requests and save them
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # enable background request intercepting:
        page.on("response", intercept_response)
        page.goto(url)
        page.wait_for_selector("[data-testid='primaryColumn']")

        # find all tweet background requests:
        user_calls = [f for f in _xhr_calls if "UserBy" in f.url]
        for uc in user_calls:
            data = uc.json()
            return data['data']['user']['result']

if __name__ == "__main__":
    # Scrapes a tweet and dumps the relevant data to a JSON
    with open("tweet_info.json", "w") as f:
        json.dump(scrape_tweet("https://x.com/stockbot2025/status/1877255965243756720"), f, indent=4)