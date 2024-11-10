# ========== SETUP AND IMPORTS ==========
import pandas as pd
import os
import yfinance as yf
from sqlalchemy import create_engine
from dotenv import load_dotenv
from tqdm import tqdm
import logging
import re
from datetime import datetime

# Setup logging to record errors to a file
logging.basicConfig(filename='data_processing_errors.log', level=logging.ERROR, 
                    format='%(asctime)s %(levelname)s:%(message)s')

# Debugging mode - set to True for debugging, DEBUG_LEVEL controls verbosity
DEBUG = True
DEBUG_LEVEL = 2  # Level 1: Basic; Level 2: Detailed

# Load environment variables for server credentials
load_dotenv('server_credentials.env')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Database engine for PostgreSQL connection
engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# Paths for input, output, and master files
new_data_paths = [
    'data/Accounts_History_2021.csv',
    'data/Accounts_History_2022.csv',
    'data/Accounts_History_2023.csv',
    'data/Accounts_History_2024.csv'
]
cleaned_data_dir = 'data/cleaned/'
master_data_path = 'master_data69.csv'

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
    review = input(f"Review the cleaned data at {consolidated_file_path}. Proceed? (y/n): ").strip().lower()
    if review != 'y':
        print("Terminating program as per user request.")
        exit()
    return consolidated_data

# ========== MASTER DATA UPDATE FUNCTION ==========
def update_master_data(cleaned_data, master_data_path, output_master_data_path):
    """Update the master_data69 file with new unique symbols."""
    try:
        if os.path.exists(master_data_path):
            master_data = pd.read_csv(master_data_path)
        else:
            master_data = pd.DataFrame(columns=['Symbol'])  # Create if not exists
        
        cleaned_data['Symbol'] = cleaned_data['Symbol'].str.upper()
        new_symbols = cleaned_data[['Symbol']].drop_duplicates()
        updated_master = pd.concat([master_data, new_symbols]).drop_duplicates(subset='Symbol')

        updated_master.to_csv(output_master_data_path, index=False)
        print(f"Updated master data saved to: {output_master_data_path}")

        review = input(f"Review the updated master data at {output_master_data_path}. Proceed? (y/n): ").strip().lower()
        if review != 'y':
            print("Terminating program as per user request.")
            exit()
        return updated_master
    except Exception as e:
        logging.error(f"Error updating master data: {e}")


# ========== ENRICH MASTER DATA FUNCTION ==========
def enrich_master_data(master_data):
    """Enrich master_data69 with additional data from Yahoo Finance."""
    enriched_data = master_data.copy()
    for idx, row in tqdm(enriched_data.iterrows(), total=enriched_data.shape[0]):
        try:
            ticker = yf.Ticker(row['Symbol'])
            info = ticker.info
            enriched_data.at[idx, 'Sector'] = info.get('sector', 'Unknown')
            enriched_data.at[idx, 'Industry'] = info.get('industry', 'Unknown')
        except Exception as e:
            logging.error(f"Error enriching symbol {row['Symbol']}: {e}")

    enriched_filepath = 'master_data69_enriched.csv'
    enriched_data.to_csv(enriched_filepath, index=False)
    print(f"Enriched master data saved to: {enriched_filepath}")

    review = input(f"Review the enriched data at {enriched_filepath}. Proceed? (y/n): ").strip().lower()
    if review != 'y':
        print("Terminating program as per user request.")
        exit()
    return enriched_data


# ========== DATABASE UPLOAD FUNCTION ==========
def upload_to_database(data):
    """Upload the enriched master_data69 to PostgreSQL database."""
    try:
        data.to_sql('master_data', con=engine, if_exists='replace', index=False)
        print("Data successfully uploaded to PostgreSQL.")
    except Exception as e:
        logging.error(f"Database upload failed: {e}")


# ========== MAIN EXECUTION ==========
if __name__ == "__main__":
    # Define file paths
    incoming_data_paths = [
        'data/Accounts_History_2021.csv',
        'data/Accounts_History_2022.csv',
        'data/Accounts_History_2023.csv',
        'data/Accounts_History_2024.csv'
    ]
    cleaned_output_path = 'data/cleaned/'
    master_data_path = 'master_data69.csv'
    output_master_data_path = 'master_data69_updated.csv'

    # Step 1: Clean Fidelity data
    cleaned_data = clean_fidelity_data(incoming_data_paths, cleaned_output_path)

    # Step 2: Update master data
    updated_master_data = update_master_data(cleaned_data, master_data_path, output_master_data_path)

    # Step 3: Enrich master data
    enriched_master_data = enrich_master_data(updated_master_data)

    # Step 4: Upload to database
    upload_to_database(enriched_master_data)

    print("Process completed successfully.")
