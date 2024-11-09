import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import re
import os
from tqdm import tqdm
import time

# ======= Configuration Section =======
# Define the expected master data file and output file paths
master_data_file = r'C:\Users\Lane\Documents\Projects\trading_bot\programs\master_data14.csv'
output_path = r'C:\Users\Lane\Documents\Projects\trading_bot\data\old data\report-weekly_symbol_status.csv'
verified_delisted_list = {"SRCL", "STER"}  # Verified Delisted List
# =====================================

# Set the date threshold dynamically to 3 days before the current date
last_known_trading_date = datetime.now() - timedelta(days=3)
print(f"Checking for delistings with last trading date on or before: {last_known_trading_date.date()}")

# Function to check if a ticker is a mutual fund using metadata from yfinance
def is_mutual_fund(ticker):
    stock = yf.Ticker(ticker)
    asset_type = stock.info.get("quoteType", "")
    return asset_type == "MUTUALFUND"

# Function to process tickers, handling cases where they start with a dash and include additional characters
def check_ticker_status(ticker, max_retries=3, delay=2):
    # Handle tickers that start with a dash by extracting the symbol
    if ticker.startswith('-'):
        # Remove the dash and capture the initial letters of the symbol (e.g., "-ABC123" becomes "ABC")
        match = re.match(r'-([A-Za-z]+)', ticker)
        if match:
            ticker = match.group(1)
            tqdm.write(f"Adjusted ticker to '{ticker}' for lookup")

    # Check if ticker is in Verified Delisted List
    if ticker in verified_delisted_list:
        message = f"{ticker}: Verified Delisted"
        tqdm.write(message)
        return "Verified Delisted"

    try:
        # Check if ticker resembles an options contract
        if re.search(r'-\w+\d+', ticker):
            return "Options Contract"

        # Check if ticker is a string of letters and numbers, indicating a 'Bought Out' case
        if re.match(r'^\d+[A-Z]+\d+$', ticker):
            return "Bought Out"

        # Determine if it's a mutual fund using metadata
        stock = yf.Ticker(ticker)
        if is_mutual_fund(ticker):
            data = stock.history(period="1mo")  # Use 1mo for mutual funds
            if not data.empty:
                message = f"{ticker}: Active (Mutual Fund)"
                tqdm.write(message)
                return "Active"
            else:
                message = f"{ticker}: Possibly Delisted (no recent data)"
                tqdm.write(message)
                return "Possibly Delisted"

        # Default handling for regular stocks
        data = stock.history(period="5d")  # Default to 5 days for regular stocks

        # Retry mechanism to handle intermittent data fetching issues
        for attempt in range(max_retries):
            if not data.empty:
                break
            if attempt < max_retries - 1:
                time.sleep(delay)
                data = stock.history(period="5d")

        # If data is still empty after retries, flag as possibly delisted
        if data.empty:
            return "Possibly Delisted"

        # Check the last available trading date without implying it's a delisting date match
        last_trading_day = data.index[-1] if not data.empty else None
        if last_trading_day and last_trading_day.to_pydatetime().date() <= last_known_trading_date.date():
            return "Possibly Delisted"

        # For regular stocks only, check if there is no volume
        if data['Volume'].sum() == 0 and not is_mutual_fund(ticker):
            return "Possibly Delisted"

        return "Active"

    except Exception:
        return "Possibly Delisted"

# Main function to check all symbols in tickers
def perform_symbol_activity_check(tickers):
    results = {}
    start_time = time.time()
    progress_bar = tqdm(tickers, desc="Checking ticker status", unit="ticker")

    # Calculate velocity and estimated time remaining
    for i, ticker in enumerate(progress_bar):
        status = check_ticker_status(ticker)
        results[ticker] = status

        # Only display important statuses, excluding "Active"
        if status != "Active":
            tqdm.write(f"{ticker}: {status}")

        # When 25% progress is reached, estimate time remaining
        if i == int(len(tickers) * 0.25):
            elapsed_time = time.time() - start_time
            velocity = i / elapsed_time
            estimated_total_time = len(tickers) / velocity
            remaining_time = estimated_total_time - elapsed_time
            progress_bar.set_postfix_str(f"Estimated time left: {int(remaining_time)}s")

        # Update estimated time left dynamically after 25% completion
        elif i > int(len(tickers) * 0.25):
            elapsed_time = time.time() - start_time
            remaining_time = (len(tickers) - i) / velocity
            progress_bar.set_postfix_str(f"Estimated time left: {int(remaining_time)}s")

    return results

# Main script execution
if __name__ == "__main__":
    # Check if the expected file exists
    if os.path.exists(master_data_file):
        # Load tickers from the specified master_data file
        master_data = pd.read_csv(master_data_file)
        tickers = master_data['symbol'].tolist()
        print(f"Running symbol activity integrity check on tickers from {master_data_file}")
        print(f"Total tickers loaded: {len(tickers)}")

        # Run the symbol activity check if tickers are loaded
        if tickers:
            results = perform_symbol_activity_check(tickers)
            
            # Save results to the specified path
            results_df = pd.DataFrame(list(results.items()), columns=['Ticker', 'Status'])
            results_df.to_csv(output_path, index=False)
            print(f"Results saved to {output_path}")
    else:
        print(f"Error: Please ensure the file '{master_data_file}' is loaded in the directory.")
