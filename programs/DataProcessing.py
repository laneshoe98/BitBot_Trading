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


# ========== FUNCTION DEFINITIONS ==========

def clean_fidelity_data(incoming_data_paths, cleaned_output_path):
    """Clean incoming Fidelity data files and consolidate them into a single file."""
    combined_data = pd.DataFrame()
    for path in incoming_data_paths:
        try:
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
            df.fillna(0, inplace=True)
            combined_data = pd.concat([combined_data, df], ignore_index=True)
            if DEBUG and DEBUG_LEVEL >= 2:
                print(f"[DEBUG] Processed file: {path}, Rows added: {df.shape[0]}")
        except Exception as e:
            logging.error(f"Error processing file {path}: {e}")

    cleaned_filepath = os.path.join(cleaned_output_path, f'cleaned_ledger_data_{datetime.now().strftime("%Y%m%d")}.csv')
    combined_data.to_csv(cleaned_filepath, index=False)
    print(f"Cleaned ledger data saved to: {cleaned_filepath}")
    review = input(f"Review the cleaned data at {cleaned_filepath}. Proceed? (y/n): ").strip().lower()
    if review != 'y':
        print("Terminating program as per user request.")
        exit()
    return combined_data


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