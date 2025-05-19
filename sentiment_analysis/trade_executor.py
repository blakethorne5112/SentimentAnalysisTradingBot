import yfinance as yf
import pandas as pd
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import argparse
import os
import json
import re
import requests
from tabulate import tabulate
from difflib import get_close_matches
import reddit_scraper as RedditScraper

def load_current_balance(filename='trading_log.json'):
    # Loads the current balance from the trading history file
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                current_balance = data.get('current_balance')
            return current_balance
        except Exception as e:
            return 20000  # Default balance if loading fails
    else:
        return 20000 # Default balance if file does not exist

def is_market_open_today():
    date = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    result = mcal.get_calendar("NYSE").schedule(start_date=date, end_date=date)
    return result.empty == False

def has_market_closed_yet():
    time = datetime.now(ZoneInfo("America/New_York")).strftime("%H:%M")
    if time >= "16:00":
        return True
    return False

def search_stock_by_name(name):
    # Searches for the stock ticker using Yahoo Finance Search API
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={name}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Filter out non-stock results
            stocks = [item for item in data.get('quotes', []) if item.get('quoteType') == 'EQUITY']
            
            if stocks:
                # Return a list of potential matches with ticker and name
                return [(stock['symbol'], stock['shortname']) for stock in stocks]
            else:
                return []
        else:
            print(f"Failed to search: Status code {response.status_code}")
            return []
    except Exception as e:
        print(f"Error searching for stock: {e}")
        return []
        
def verify_stock_exists(ticker_or_name):
    # Verifies if a stock ticker or name exists
    if ticker_or_name.isupper() and len(ticker_or_name) <= 5:
        try:
            ticker = yf.Ticker(ticker_or_name)
            info = ticker.info
            if 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
                return True, ticker_or_name, info.get('shortName', 'Unknown')
        except Exception:
            pass
    
    results = search_stock_by_name(ticker_or_name)
    
    if results:
        ticker, name = results[0]
        return True, ticker, name
    else:
        # Tries to find close matches using list of popular stocks for comparison
        try:
            url = "https://query2.finance.yahoo.com/v1/finance/trending/US"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                popular_stocks = [quote['symbol'] for quote in data.get('finance', {}).get('result', [{}])[0].get('quotes', [])]
                
                common_names = ["Apple", "Microsoft", "Google", "Amazon", "Tesla", "Facebook", "Netflix", "Nvidia"]
                
                # Check for close matches
                close_match = get_close_matches(ticker_or_name.lower(), [name.lower() for name in common_names], n=1, cutoff=0.6)
                
                if close_match:
                    matched_name = common_names[[name.lower() for name in common_names].index(close_match[0])]
                    return False, None, f"Did you mean '{matched_name}'?"
        except Exception as e:
            pass
            
        return False, None, "Stock not found"

def get_stock_from_user_input(input_text, allow_selection=True):
    # Processes user input for stock name/ticker and returns a valid ticker
    exists, ticker, name_or_message = verify_stock_exists(input_text)
    
    if exists:
        print(f"Found: {name_or_message} ({ticker})")
        return ticker
    else:
        # If there was a suggestion
        if "Did you mean" in name_or_message and allow_selection:
            suggested_name = re.search(r"'(.*?)'", name_or_message).group(1)
            confirm = input(f"{name_or_message} (y/n): ")
            if confirm.lower() == 'y':
                # Try with the suggested name
                return get_stock_from_user_input(suggested_name)
        
        print(f"Error: {name_or_message}")
        return None
    
def trade_from_sentiment_analysis(ticker, date, filename="sentiment_log.json"):
    try:
        with open(filename, 'r') as f:
            sentiment_data = json.load(f)
        for entry in sentiment_data.get("logs", []):
            if entry["stock_name"] == ticker.upper() and entry["date"] == date:
                if float(entry["sentiment"]) >= 5:
                    return "BUY"
                elif float(entry["sentiment"]) < 5:
                    return "SHORT"
        print(f"No sentiment data available for {ticker} on {date}")
        return None
    except FileNotFoundError:
        print(f"Sentiment data file not found: {filename}")
        return None
    except Exception as e:
        print(f"Error reading sentiment data: {e}")
        return None

class PracticeTrader:
    def __init__(self, initial_balance=20000):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.transaction_history = []
        self.load_history()
    
    def load_history(self, filename='trading_log.json'):
        # Loads transaction history from file if it exists
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    self.transaction_history = data.get('transactions', [])
                    self.current_balance = data.get('current_balance', self.initial_balance)
                print(f"Loaded trading history with {len(self.transaction_history)} previous transactions")
                print(f"Current balance: ${self.current_balance:.2f}")
            except Exception as e:
                print(f"Error loading history: {e}")
    
    def save_history(self, filename='trading_log.json'):
        # Saves transaction history to file
        data = {
            'transactions': self.transaction_history,
            'current_balance': self.current_balance,
        }
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved trading history to {filename}")
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def get_stock_data(self, ticker, date):
        # Gets open and close price data for the date
        start_date = pd.Timestamp(date)
        end_date = start_date + timedelta(days=1)
        
        try:
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if data.empty:
                print(f"No data available for {ticker} on {date}")
                return None, None
            
            # Convert Series values to float before returning
            open_price = float(data['Open'].iloc[0])
            close_price = float(data['Close'].iloc[0])
            
            return open_price, close_price
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None, None
    
    def record_transaction(self, ticker, action, price, shares, date, time_of_day, investment_amount=None):
        # Records a transaction to the history
        transaction_amount = price * shares
        
        if action == "BUY":
            cost = transaction_amount
            if cost > self.current_balance:
                print(f"Insufficient funds! You need ${cost:.2f} but have ${self.current_balance:.2f}")
                return False
            self.current_balance -= cost
        
        elif action == "SHORT":
            proceeds = transaction_amount
            self.current_balance += proceeds

        # Record the transaction
        transaction = {
            'ticker': ticker,
            'action': action,
            'price': price,
            'shares': shares,
            'amount': transaction_amount,
            'date': date,
            'time': time_of_day,
            'balance_after': self.current_balance
        }
        if investment_amount:
            transaction['investment_amount'] = investment_amount
            
        self.transaction_history.append(transaction)
        
        return True
    
    def trade(self, ticker, date, investment_amount, action_open='BUY'):
        # Executes a set of trades with a specific dollar amount - either buys the full amount at open and sells the full amount at close or vice versa
        open_price, close_price = self.get_stock_data(ticker, date)
        
        if open_price is None or close_price is None:
            print(f"Cannot execute trade for {ticker} on {date} due to missing data")
            return
        
        # Calculate shares to buy/sell based on investment amount
        if investment_amount > self.current_balance:
            print(f"Insufficient funds! You wanted to invest ${investment_amount:.2f} but have ${self.current_balance:.2f}")
            return
            
        shares = investment_amount / open_price
        
        print(f"\n--- Trading {ticker} on {date} ---")
        print(f"Open price: ${open_price:.2f}")
        print(f"Close price: ${close_price:.2f}")
        print(f"Investment amount: ${investment_amount:.2f}")
        print(f"Shares: {shares:.6f}")
        
        # Determine actions based on input
        action_open = action_open.upper()
        action_close = "SHORT" if action_open == "BUY" else "BUY"
        
        # Execute open transaction
        print(f"\nExecuting {action_open} of {shares:.6f} shares of {ticker} at open (${open_price:.2f})")
        if not self.record_transaction(ticker, action_open, open_price, shares, date, "OPEN", investment_amount):
            return
        
        # Execute close transaction
        print(f"Executing {action_close} of {shares:.6f} shares of {ticker} at close (${close_price:.2f})")
        if not self.record_transaction(ticker, action_close, close_price, shares, date, "CLOSE"):
            return
        
        # Calculate profit/loss
        if action_open == "BUY":
            cost = open_price * shares
            proceeds = close_price * shares
            profit = proceeds - cost
        else:  # SELL at open
            proceeds = open_price * shares
            cost = close_price * shares
            profit = proceeds - cost
        
        print(f"\nTrade Summary:")
        print(f"{'Bought' if action_open == 'BUY' else 'Sold'} at open: ${(open_price * shares):.2f}")
        print(f"{'Sold' if action_open == 'BUY' else 'Bought'} at close: ${(close_price * shares):.2f}")
        print(f"Day's Profit/Loss: ${profit:.2f} ({profit/cost*100:.2f}%)")
        print(f"Current Balance: ${self.current_balance:.2f}")
        
        # Save history after trade
        self.save_history()
        
        return profit
    
    def show_trade_history(self, limit=10):
        """Display recent trade history"""
        print(f"\n--- Recent Trade History (Last {min(limit, len(self.transaction_history))}) ---")
        if not self.transaction_history:
            print("No trade history")
            return
        
        history_data = []
        for i, transaction in enumerate(reversed(self.transaction_history[-limit:])):
            shares_str = f"{transaction['shares']:.6f}"
            row = [
                transaction['date'],
                transaction['time'],
                transaction['ticker'],
                transaction['action'],
                shares_str,
                f"${transaction['price']:.2f}",
                f"${transaction['amount']:.2f}",
                f"${transaction['balance_after']:.2f}"
            ]
            # Include investment amount if available
            if 'investment_amount' in transaction:
                row.append(f"${transaction['investment_amount']:.2f}")
            else:
                row.append("N/A")
                
            history_data.append(row)
        
        headers = ["Date", "Time", "Ticker", "Action", "Shares", "Price", "Amount", "Balance", "Investment"]
        print(tabulate(history_data, headers=headers, tablefmt="grid"))
    
    def show_performance(self):
        """Display overall performance"""
        print("\n--- Trading Performance ---")
        
        if not self.transaction_history:
            print("No trade history to analyze")
            return
        
        # Calculate statistics
        total_trades = len(self.transaction_history) // 2  # Counting open/close pairs as one trade
        
        # Calculate profit from completed trades
        trades = []
        i = 0
        while i < len(self.transaction_history):
            if i + 1 < len(self.transaction_history):
                open_tx = self.transaction_history[i]
                close_tx = self.transaction_history[i+1]
                
                if open_tx['ticker'] == close_tx['ticker'] and open_tx['date'] == close_tx['date']:
                    if open_tx['action'] == 'BUY':
                        buy_amount = open_tx['amount']
                        sell_amount = close_tx['amount']
                    else:
                        sell_amount = open_tx['amount']
                        buy_amount = close_tx['amount']
                    
                    profit = sell_amount - buy_amount
                    # Use investment_amount if available
                    investment = open_tx.get('investment_amount', buy_amount)
                    
                    trades.append({
                        'ticker': open_tx['ticker'],
                        'date': open_tx['date'],
                        'profit': profit,
                        'profit_pct': (profit / investment) * 100,
                        'investment': investment
                    })
                
                i += 2
            else:
                i += 1
        
        # Calculate performance metrics
        if trades:
            profits = [t['profit'] for t in trades]
            total_profit = sum(profits)
            profit_loss = self.current_balance - self.initial_balance
            avg_profit = total_profit / len(trades)
            win_count = sum(1 for p in profits if p > 0)
            loss_count = sum(1 for p in profits if p < 0)
            win_rate = (win_count / len(trades)) * 100 if trades else 0
            
            # Find best and worst trades
            best_trade = max(trades, key=lambda x: x['profit_pct']) if trades else None
            worst_trade = min(trades, key=lambda x: x['profit_pct']) if trades else None
            
            print(f"Initial Balance: ${self.initial_balance:.2f}")
            print(f"Current Balance: ${self.current_balance:.2f}")
            print(f"Profit/Loss: {'-$' if profit_loss < 0 else '$'}{abs(profit_loss):.2f}")
            print(f"Total Completed Trades: {len(trades)}")
            print(f"Win Rate: {win_rate:.2f}% ({win_count} wins, {loss_count} losses)")
            print(f"Average Profit per Trade: ${avg_profit:.2f}")
            
            if best_trade:
                print(f"Best Trade: {best_trade['ticker']} on {best_trade['date']} (${best_trade['profit']:.2f}, {best_trade['profit_pct']:.2f}%)")
            if worst_trade:
                print(f"Worst Trade: {worst_trade['ticker']} on {worst_trade['date']} (${worst_trade['profit']:.2f}, {worst_trade['profit_pct']:.2f}%)")
        else:
            print("No completed trades to analyze")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Practice Stock Trading Simulator')
    parser.add_argument('--ticker', type=str, help='Stock ticker symbol')
    parser.add_argument('--date', type=str, help='Trade date (YYYY-MM-DD)')
    parser.add_argument('--amount', type=float, help='Dollar amount to invest')
    parser.add_argument('--action', type=str, default='BUY', choices=['BUY', 'SHORT'], 
                        help='Action to take at market open (BUY or SHORT, default: BUY)')
    parser.add_argument('--history', action='store_true', help='Show trade history')
    parser.add_argument('--performance', action='store_true', help='Show performance metrics')
    return parser.parse_args()


def main():
    args = parse_arguments()
    trader = PracticeTrader()
    
    if args.history:
        trader.show_trade_history()
    
    if args.performance:
        trader.show_performance()
    
    # If ticker, date, and amount provided, execute a trade
    if args.ticker and args.date and args.amount:
        try:
            # Validate date format
            trade_date = datetime.strptime(args.date, '%Y-%m-%d').strftime('%Y-%m-%d')
            
            # Execute the trade
            ticker = args.ticker.upper()
            trader.trade(ticker, trade_date, args.amount, args.action)
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")
    
    # If no arguments provided, go into the main menu
    if not any([args.ticker and args.date and args.amount, args.history, args.performance]):
        menu(trader)
        
def menu(trader):
    print("\n=== Stock Practice Trading ===")
    
    while True:
        print("\nOptions:")
        print("1. Execute trade")
        print("2. View trade history")
        print("3. View performance metrics")
        print("4. Run sentiment analysis")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            if not has_market_closed_yet() or not is_market_open_today():
                closed_input = input("Market is either not trading today or has not closed yet for the day. Would you like to practice trade on a past date? (y/n): ")
                if closed_input.lower() == 'y':
                    date_input = input("Enter date (YYYY-MM-DD): ")
                    try:
                        date = datetime.strptime(date_input, '%Y-%m-%d').strftime('%Y-%m-%d')
                    except ValueError:
                        print("Invalid date format. try again.")
                        continue
                else:
                    print("Exiting. Your trading data has been saved.")
                    break
            stock_input = input("Enter stock name (eg. Tesla): ")
            ticker = get_stock_from_user_input(stock_input)
            if not date:
                date = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
            
            try:
                # Get dollar amount to invest
                investment_amount = float(load_current_balance() / 2)
                if investment_amount <= 0:
                    print("Investment amount must be positive.")
                    continue

                sentiment_input = input("Would you like to trade based on sentiment analysis of the company for the day? (y/n): ")
                if sentiment_input.lower() == 'y':
                    action = trade_from_sentiment_analysis(ticker, date)
                else:
                    action = input("Action at open (BUY/SHORT, default: BUY): ").upper() or "BUY"
                    if action not in ["BUY", "SHORT"]:
                        print("Invalid action. Using BUY.")
                        action = "BUY"
                # Execute trade
                trader.trade(ticker, date, investment_amount, action)
            except ValueError as e:
                print(f"Invalid input: {e}")
        
        elif choice == '2':
            limit = input("How many transactions to show? (default: 10): ")
            try:
                limit = int(limit) if limit else 10
                trader.show_trade_history(limit)
            except ValueError:
                print("Invalid input. Showing 10 transactions.")
                trader.show_trade_history(10)
        
        elif choice == '3':
            trader.show_performance()
        
        elif choice == '4':
            RedditScraper.main()

        elif choice == '5':
            print("Exiting. Your trading data has been saved.")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()