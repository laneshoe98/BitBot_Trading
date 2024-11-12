# ========== SETTINGS ==========
# Configurable settings for review mode, debugging, and data update behavior

SETTINGS = {
    "REVIEW_MODE": True,            # If True, program prompts for review; if False, auto-updates without prompts
    "DEBUG": True,                  # If True, print debug statements; if False, suppress debug output
    "REVIEW_FREQUENCY": 10,         # Number of rows to process before pausing for review
    "FILL_ONLY_IF_BLANK": True,     # If True, only fills blank values in master_data69_updated
    "REPORT_INCOMPLETE_ROWS": True  # If True, displays rows with missing data for review
}
import pandas as pd
import os
import logging
import yfinance as yf
from datetime import datetime

# Setup logging to record errors to a file
logging.basicConfig(filename='cleaning_errors.log', level=logging.ERROR, 
                    format='%(asctime)s %(levelname)s:%(message)s')

# Paths for input and output directories
new_data_paths = [
    'data/raw/Accounts_History_2021.csv',
    'data/raw/Accounts_History_2022.csv',
    'data/raw/Accounts_History_2023.csv',
    'data/raw/Accounts_History_2024.csv'
]
output_dir = 'data/cleaned/'
master_data_path = 'master_data69.csv'  # Path to the master data file

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# ========== DATA CLEANING FUNCTION ==========
def clean_data(file_paths, output_dir):
    """Cleans multiple Fidelity data files, consolidates them, 
    and saves the cleaned data as cleaned_assets_ledger_data_<timestamp>.csv"""
    combined_data = []  # List to store each cleaned DataFrame

    for file_path in file_paths:
        try:
            data = pd.read_csv(file_path)
            if SETTINGS["DEBUG"]:
                print(f"[DEBUG] Loaded {file_path} with {data.shape[0]} rows")

            # Standard cleaning process: remove extra spaces, drop rows with no symbol, rename columns
            data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            data = data.dropna(subset=['Symbol'])
            
            rename_columns = {
                'Run Date': 'transaction_date', 'Account': 'portfolio_name', 'Action': 'notes', 
                'Symbol': 'symbol', 'Description': 'asset_name', 'Quantity': 'quantity', 
                'Price': 'price', 'Amount': 'transaction_amount', 'Commission': 'commission', 'Fees': 'fees'
            }
            data = data.rename(columns=rename_columns)

            # Fill missing values in financial columns
            data['commission'] = data['commission'].fillna(0)
            data['fees'] = data['fees'].fillna(0)

            # Drop unnecessary columns
            data.drop(columns=['Type', 'Exchange Quantity', 'Exchange Currency', 'Currency', 
                               'Exchange Rate', 'Accrued Interest', 'Settlement Date'], inplace=True, errors='ignore')

            # Keep only the columns we want in the final version
            final_columns_order = ['symbol', 'asset_name', 'quantity', 'price', 'transaction_amount', 
                                   'commission', 'fees', 'portfolio_name', 'transaction_date', 'notes']
            data = data[final_columns_order]

            # Ensure transaction dates are in a uniform format
            data['transaction_date'] = pd.to_datetime(data['transaction_date'], format='%m/%d/%Y').dt.strftime('%Y/%m/%d')
            data['symbol'] = data['symbol'].str.lstrip('-')  # Remove any leading dashes from symbols

            # Append the cleaned DataFrame to the combined list
            combined_data.append(data)

        except Exception as e:
            logging.error(f"Error during data cleaning for {file_path}: {e}")
            if SETTINGS["DEBUG"]:
                print(f"[DEBUG] Error during data cleaning for {file_path}: {e}")

    # Concatenate all cleaned data files into a single DataFrame
    consolidated_data = pd.concat(combined_data, ignore_index=True)

    # Generate a timestamped output file name
    timestamp = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(output_dir, f"cleaned_assets_ledger_data_{timestamp}.csv")

    # Save the cleaned consolidated data
    consolidated_data.to_csv(output_file, index=False)
    if SETTINGS["DEBUG"]:
        print(f"[DEBUG] cleaned_assets_ledger_data_{timestamp}.csv saved in dir {output_dir}. Please review.")
        input("Press Enter to get basic information about these symbols...")
    
    return consolidated_data

# ========== UPDATE MASTER DATA FUNCTION ==========
def update_master_data(consolidated_data, master_data_path, output_dir):
    """Updates the master data file with new symbols from the consolidated data and fetches additional data from yfinance."""
    try:
        # Load the master data file
        master_data = pd.read_csv(master_data_path)
        if SETTINGS["DEBUG"]:
            print(f"[DEBUG] Loaded master data with {master_data.shape[0]} rows")
        
        # Find new symbols not in master data
        new_symbols = consolidated_data[~consolidated_data['symbol'].isin(master_data['symbol'])]
        
        # Prompt user to review new symbols before proceeding, if review mode is enabled
        if SETTINGS["REVIEW_MODE"]:
            print("[REVIEW] New symbols identified:")
            print(new_symbols['symbol'].unique())
            input("Press Enter to continue with data fetching...")

        # Append new symbols to the master data
        updated_master_data = pd.concat([master_data, new_symbols], ignore_index=True)
        
        # Fetch sector, industry, and first traded date for new symbols using yfinance
        for i, symbol in enumerate(new_symbols['symbol'].unique(), 1):
            try:
                ticker = yf.Ticker(symbol)
                sector = ticker.info.get('sector')
                industry = ticker.info.get('industry')
                
                # Get historical data to find the first traded date
                hist_data = ticker.history(period="max")
                first_traded = hist_data.index[0].strftime('%Y/%m/%d') if not hist_data.empty else None

                # Fill only if blanks if the setting is enabled
                if SETTINGS["FILL_ONLY_IF_BLANK"]:
                    if pd.isna(updated_master_data.loc[updated_master_data['symbol'] == symbol, 'sector']).all():
                        updated_master_data.loc[updated_master_data['symbol'] == symbol, 'sector'] = sector
                    if pd.isna(updated_master_data.loc[updated_master_data['symbol'] == symbol, 'industry']).all():
                        updated_master_data.loc[updated_master_data['symbol'] == symbol, 'industry'] = industry
                    if pd.isna(updated_master_data.loc[updated_master_data['symbol'] == symbol, 'first_traded']).all():
                        updated_master_data.loc[updated_master_data['symbol'] == symbol, 'first_traded'] = first_traded
                else:
                    updated_master_data.loc[updated_master_data['symbol'] == symbol, 'sector'] = sector
                    updated_master_data.loc[updated_master_data['symbol'] == symbol, 'industry'] = industry
                    updated_master_data.loc[updated_master_data['symbol'] == symbol, 'first_traded'] = first_traded

                # Display the fetched data in CSV format
                print(f"{symbol},{sector},{industry},{first_traded}")

                # Review every 10 rows if in review mode
                if SETTINGS["REVIEW_MODE"] and i % SETTINGS["REVIEW_FREQUENCY"] == 0:
                    input(f"[REVIEW] Press Enter to continue after reviewing {i} rows...")

            except Exception as e:
                logging.error(f"Error fetching data for {symbol}: {e}")
                if SETTINGS["DEBUG"]:
                    print(f"[DEBUG] Error fetching data for {symbol}: {e}")

        # Prompt user to review the final updated master data if in review mode
        if SETTINGS["REVIEW_MODE"]:
            print("[REVIEW] Final version of updated master data:")
            print(updated_master_data.tail())
            input("Press Enter to save the final updated master data...")

        # Save the updated master data with a new name
        updated_master_data_path = os.path.join(output_dir, "master_data69_updated.csv")
        updated_master_data.to_csv(updated_master_data_path, index=False)
        
        if SETTINGS["DEBUG"]:
            print(f"[DEBUG] Updated master data saved to {updated_master_data_path}")

    except Exception as e:
        logging.error(f"Error updating master data: {e}")
        if SETTINGS["DEBUG"]:
            print(f"[DEBUG] Error updating master data: {e}")

# ========== MAIN EXECUTION ==========
if __name__ == "__main__":
    # Clean the new data
    consolidated_data = clean_data(new_data_paths, output_dir)
    
    # Update the master data with any new symbols found and fill in missing information
    update_master_data(consolidated_data, master_data_path, output_dir)
