# ========== SETUP AND IMPORTS ==========
import pandas as pd
import os
import yfinance as yf
from sqlalchemy import create_engine
from dotenv import load_dotenv
from tqdm import tqdm
from pathlib import Path
import logging
import time
import re
from datetime import datetime

# Setup logging to record errors to a file
logging.basicConfig(filename='data_processing_errors.log', level=logging.ERROR, 
                    format='%(asctime)s %(levelname)s:%(message)s')

# Debugging mode - set to True for debugging, DEBUG_LEVEL controls verbosity
DEBUG = True
DEBUG_LEVEL = 2  # Level 1: Basic; Level 2: Detailed

# Load environment variables for server credentials
load_dotenv(r'C:\Users\Lane\Documents\Projects\trading_bot\programs\server_credentials.env')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Database engine for PostgreSQL connection
engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# Paths for input, output, and master files
new_data_paths = [
    r'C:\Users\Lane\Documents\Projects\trading_bot\data\old data\Accounts_History_2021.csv',
    r'C:\Users\Lane\Documents\Projects\trading_bot\data\old data\Accounts_History_2022.csv',
    r'C:\Users\Lane\Documents\Projects\trading_bot\data\old data\Accounts_History_2023.csv',
    r'C:\Users\Lane\Documents\Projects\trading_bot\data\old data\Accounts_History_2024.csv'
]
cleaned_data_dir = r'C:\Users\Lane\Documents\Projects\trading_bot\data\old data'
master_data_path = r'C:\Users\Lane\Documents\Projects\trading_bot\programs\master_data14.csv'
report_path = r'C:\Users\Lane\Documents\Projects\trading_bot\data\old data\symbol_verification_report.csv'

# ========== VERSION INCREMENT FUNCTION ==========
def increment_filename_version(file_path):
    """Increments the version number in a file name."""
    path = Path(file_path)
    base_name = path.stem
    version_num = ''.join(filter(str.isdigit, base_name))
    version = int(version_num) if version_num else 0
    new_version = version + 1
    new_name = base_name.rstrip('0123456789') + str(new_version)
    if DEBUG and DEBUG_LEVEL >= 1:
        print(f"[DEBUG] New versioned filename: {new_name}")
    return path.with_name(new_name).with_suffix(path.suffix)

# ========== DATA CLEANING FUNCTION ==========
def clean_data(file_paths, cleaned_dir):
    """Cleans multiple Fidelity data files, combines them into one consolidated file, 
    and saves it as cleaned_account_history_<timestamp>.csv."""
    combined_data = []  # List to store each cleaned DataFrame

    for file_path in file_paths:
        try:
            data = pd.read_csv(file_path)
            if DEBUG and DEBUG_LEVEL >= 1:
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
            data['commission'] = data['commission'].fillna(0)
            data['fees'] = data['fees'].fillna(0)

            # Drop columns we don't need for the master data
            data.drop(columns=['Type', 'Exchange Quantity', 'Exchange Currency', 'Currency', 'Exchange Rate', 
                               'Accrued Interest', 'Settlement Date'], inplace=True, errors='ignore')
            
            # Keep only the columns we want in the final version
            final_columns_order = ['symbol', 'asset_name', 'quantity', 'price', 'transaction_amount', 
                                   'commission', 'fees', 'portfolio_name', 'transaction_date', 'notes']
            data = data[final_columns_order]

            # Ensure transaction dates are in a uniform format
            data['transaction_date'] = pd.to_datetime(data['transaction_date'], format='%m/%d/%Y').dt.strftime('%Y-%m-%d')
            data['symbol'] = data['symbol'].str.lstrip('-')  # Remove any leading dashes from symbols

            # Append the cleaned DataFrame to the combined list
            combined_data.append(data)

        except Exception as e:
            logging.error(f"Error during data cleaning for {file_path}: {e}")
            if DEBUG and DEBUG_LEVEL >= 2:
                print(f"[DEBUG] Error during data cleaning for {file_path}: {e}")

    # Concatenate all cleaned data files into a single DataFrame
    consolidated_data = pd.concat(combined_data, ignore_index=True)
    
    # Generate a timestamped filename and save the consolidated data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    consolidated_file_path = os.path.join(cleaned_dir, f"cleaned_account_history_{timestamp}.csv")
    consolidated_data.to_csv(consolidated_file_path, index=False)
    
    print(f"Consolidated cleaned data saved as: {consolidated_file_path}")
    return consolidated_file_path  # Return path for reference

# ========== MASTER DATA UPDATE FUNCTION ==========
def update_master_data(cleaned_data_files, master_data_path):
    """Adds symbols from cleaned files to master data, ensuring only valid symbols are added."""
    try:
        # Load existing master data if it exists, or create an empty DataFrame
        if os.path.exists(master_data_path):
            master_data = pd.read_csv(master_data_path)
        else:
            master_data = pd.DataFrame(columns=['symbol'])

        # Set of existing symbols in the master data for quick comparison
        master_symbols_set = set(master_data['symbol'].str.upper())  # Standardized to uppercase for comparison

        # Regular expression to filter out non-standard symbols
        # This pattern will match symbols with 1-5 uppercase letters, as typical stock symbols
        stock_symbol_pattern = re.compile(r'^[A-Z]{1,5}$')

        # Collect valid symbols from cleaned data files
        new_symbols_set = set()
        for data in cleaned_data_files:
            cleaned_symbols = data['symbol'].str.upper()  # Convert to uppercase for case-insensitive comparison
            # Filter symbols based on regex pattern
            valid_symbols = cleaned_symbols[cleaned_symbols.str.match(stock_symbol_pattern)]
            new_symbols_set.update(valid_symbols)

        # Identify unique new symbols that are not already in master data
        unique_new_symbols = new_symbols_set - master_symbols_set

        # Create a DataFrame for the new symbols
        new_entries = pd.DataFrame({'symbol': list(unique_new_symbols)})
        
        # Concatenate the new entries with the master data
        updated_data = pd.concat([master_data, new_entries], ignore_index=True)

        # Save the updated master data with a new version
        new_master_data_path = increment_filename_version(master_data_path)
        updated_data.to_csv(new_master_data_path, index=False)
        print(f"New master data created and saved as: {new_master_data_path}")
        
        return new_master_data_path  # Return path for the enrichment step

    except Exception as e:
        logging.error(f"Error during master data update: {e}")
        if DEBUG and DEBUG_LEVEL >= 2:
            print(f"[DEBUG] Error during master data update: {e}")
        return None


# ========== ENRICH MASTER DATA WITH YFINANCE ==========
def enrich_master_data(master_data):
    """Enriches the master data with additional information from YFinance, handling cases with missing data.
       Filters out non-standard symbols to avoid enriching symbols that YFinance doesn't recognize.
    """
    master_data['longname'] = None
    master_data['sector'] = None
    master_data['industry'] = None
    master_data['first_traded'] = None

    for idx, symbol in enumerate(tqdm(master_data['symbol'].unique(), desc="Enriching data", unit="symbol")):
        try:
            stock = yf.Ticker(symbol)
            info = stock.info

            longname = info.get('longName', 'Unknown')
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            history = stock.history(period="max")
            first_traded = history.index.min().strftime('%Y-%m-%d') if not history.empty else 'Unknown'

            master_data.loc[master_data['symbol'] == symbol, ['longname', 'sector', 'industry', 'first_traded']] = [
                longname, sector, industry, first_traded
            ]

            if DEBUG and DEBUG_LEVEL >= 2 and idx % 50 == 0:
                print(f"[DEBUG] Enriched symbol {symbol}: longname={longname}, sector={sector}, industry={industry}")

        except Exception as e:
            logging.error(f"Error enriching symbol {symbol}: {e}")
            if DEBUG and DEBUG_LEVEL >= 2:
                print(f"[DEBUG] Error enriching symbol {symbol}: {e}")
            master_data.loc[master_data['symbol'] == symbol, ['longname', 'sector', 'industry', 'first_traded']] = [
                'Unknown', 'Unknown', 'Unknown', 'Unknown'
            ]
    return master_data

# ========== DATABASE UPLOAD WITH USER PROMPT ==========
def upload_to_database(data):
    """Prompts the user to confirm if they want to upload the enriched master data to PostgreSQL."""
    user_input = input("Do you want to upload the data to PostgreSQL? (y/n): ").strip().lower()
    if user_input == 'y':
        try:
            data.to_sql('asset_ledger', con=engine, if_exists='append', index=False)
            print("Data successfully inserted into the database.")
            print("Program run successfully, symbol verification report generated, new master_data file created, uploaded to PostgreSQL.")
        except Exception as e:
            logging.error(f"Error during database upload: {e}")
            if DEBUG and DEBUG_LEVEL >= 2:
                print(f"[DEBUG] Error during database upload: {e}")
    else:
        print("Program run successfully, symbol verification report generated, new master_data file created, not uploaded to PostgreSQL.")

# ========== MAIN SCRIPT EXECUTION ==========
if __name__ == "__main__":
    # Step 1: Clean the new data files
    cleaned_data_files = clean_data(new_data_paths, cleaned_data_dir)
    if cleaned_data_files:
        if DEBUG and DEBUG_LEVEL >= 1:
            print(f"[DEBUG] Total cleaned files processed: {len(cleaned_data_files)}")

        # Step 2: Update master data with new symbols, creating the next version before enrichment
        new_master_data_path = update_master_data(cleaned_data_files, master_data_path)
        if new_master_data_path:
            print(f"New master data file created: {new_master_data_path}")

            # Prompt user to confirm before proceeding with enrichment and database upload
            proceed = input("Do you want to proceed with enrichment and database upload? (y/n): ").strip().lower()
            if proceed != 'y':
                print("Process terminated by user after master data generation. No enrichment or upload performed.")
                exit()  # Exit the program if user does not wish to proceed

            # Step 3: Load and enrich the new master data file, then save enriched data to the same file
            master_data = pd.read_csv(new_master_data_path)
            enriched_master_data = enrich_master_data(master_data)
            enriched_master_data.to_csv(new_master_data_path, index=False)
            print(f"Enriched master data saved to: {new_master_data_path}")
            
            # Step 4: Prompt for database upload
            upload_to_database(enriched_master_data)
