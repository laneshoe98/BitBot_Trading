# %%

# ========== SETTINGS ==========
# Configuration settings for debugging and data update behavior
SETTINGS = {
    "DEBUG": True,                  # If True, print debug statements; if False, suppress debug output
    "DATA_SOURCE": "yfinance",      # Source of historical data (yfinance or other API)
    "SAVE_FORMAT": "json",          # Format to save the collected data
}

import pandas as pd
import json
import yfinance as yf
import os
from datetime import datetime

# Paths for saving data
output_dir = '1_data/collected/'   # Directory to save collected data
os.makedirs(output_dir, exist_ok=True)

print("Setup complete. Ready to collect data for BitBot!")


# %%

# ========== DATA COLLECTION FUNCTION ==========
# This function collects historical Bitcoin data for multiple default timeframes,
# starting from the earliest available date. It saves data month-by-month, allowing for review at year-end.

from tqdm import tqdm
import time

def collect_bitcoin_data(output_dir):
    # Initialize ticker symbol and default timeframes
    ticker = "BTC-USD"  # Bitcoin ticker symbol for Yahoo Finance
    timeframes = ["1m", "15m", "1h", "1d", "1mo"]  # Default timeframes
    collected_data = {}  # Dictionary to store data for each year

    # Get the first traded date for Bitcoin from Yahoo Finance
    ticker_info = yf.Ticker(ticker)
    hist_data = ticker_info.history(period="max", interval="1mo")
    first_date = hist_data.index[0].strftime('%Y-%m-%d')
    start_year = int(first_date[:4])

    current_year = datetime.now().year

    # Loop over each year from the start date to the current year
    for year in range(start_year, current_year + 1):
        yearly_data = {tf: [] for tf in timeframes}  # Data for the current year

        print(f"Collecting data for year {year}...")
        for month in range(1, 13):  # Loop over each month
            month_str = f"{year}-{month:02d}-01"
            for tf in timeframes:  # Loop over each timeframe
                try:
                    # Fetch one month's worth of data for each timeframe
                    data = yf.download(ticker, start=month_str, end=f"{year}-{month+1:02d}-01", interval=tf)
                    data.reset_index(inplace=True)
                    
                    # Store each month's data within the year
                    if not data.empty:
                        monthly_json = data.to_json(orient="records", date_format="iso")
                        yearly_data[tf].append(monthly_json)

                        # Display progress every month
                        print(f"Collected {tf} data for {year}-{month:02d} with {len(data)} rows")

                except Exception as e:
                    print(f"Error collecting {tf} data for {year}-{month:02d}: {e}")
                    return

            # Save month-by-month JSON
            json_filename = os.path.join(output_dir, f"bitcoin_data_{year}.json")
            with open(json_filename, 'w') as f:
                json.dump(yearly_data, f)
            print(f"[DEBUG] Saved monthly data for {year}-{month:02d}")

        # Save at year-end and provide data review
        json_filename = os.path.join(output_dir, f"bitcoin_data_{year}.json")
        with open(json_filename, 'w') as f:
            json.dump(yearly_data, f)

        print(f"[DEBUG] Yearly data for {year} saved successfully.")
        
        # Prompt for review at end of year
        print(f"Please review the data for {year} before proceeding.")
        input("If everything looks good, press Enter to continue, or press Ctrl+C to abort and review.")
    
    return collected_data


# %%
# ========== ITERATIVE TROUBLESHOOTING CELL ==========
# This cell helps improve any selected notebook cell iteratively, based on ChatGPT's API suggestions.
# It saves iterative improvements to a separate notebook file, preserving the original.

# Import the troubleshooter module
from troubleshooter import troubleshoot_cell

# Specify which cell you want to troubleshoot (set the index here)
cell_index_to_troubleshoot = 2  # Example: set to the cell you want to improve

# Call the troubleshooting function to start the interactive process
troubleshoot_cell(cell_index_to_troubleshoot)

# %%

# ========== EXECUTE DATA COLLECTION ==========
# Run the data collection and save results
collected_data = collect_bitcoin_data(output_dir)
print("Data collection complete.")



