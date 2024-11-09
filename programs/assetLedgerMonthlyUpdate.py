# Preamble: This script is used to clean and insert monthly asset ledger data into a PostgreSQL database.
import pandas as pd
import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv(r'C:\Users\Lane\Documents\Projects\trading_bot\programs\server_credentials.env')
file_path = r'C:\\Users\\Lane\\Documents\\Projects\\trading_bot\\data\\old data\\Accounts_History_2023.csv'  # Update this path as needed
data = pd.read_csv(file_path)

# Step 1: Clean and Format the Data
data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
data = data.dropna(subset=['Symbol'])  # 'Symbol' is renamed to 'symbol' 
rename_columns = {
    'Run Date': 'transaction_date',
    'Account': 'portfolio_name',
    'Action': 'notes',
    'Symbol': 'symbol',
    'Description': 'asset_name',
    'Quantity': 'quantity',
    'Price': 'price',
    'Amount': 'transaction_amount',
    'Commission': 'commission',
    'Fees': 'fees'
}
data = data.rename(columns=rename_columns)
data['commission'] = data['commission'].fillna(0)
data['fees'] = data['fees'].fillna(0)
columns_to_delete = [
    'Type', 'Exchange Quantity', 'Exchange Currency', 'Currency', 
    'Exchange Rate', 'Accrued Interest', 'Settlement Date'
]
data = data.drop(columns=columns_to_delete, errors='ignore')
final_columns_order = [
    'symbol', 'asset_name', 'quantity', 'price', 'transaction_amount', 
    'commission', 'fees', 'portfolio_name', 'transaction_date', 'notes'
]
data = data[final_columns_order]
data['transaction_date'] = pd.to_datetime(data['transaction_date'], format='%m/%d/%Y').dt.strftime('%Y-%m-%d')
data['symbol'] = data['symbol'].str.lstrip('-')

# Generate the _cleaned.csv File
cleaned_file_path = os.path.splitext(file_path)[0] + '_cleaned.csv'
data.to_csv(cleaned_file_path, index=False)
print(f"Cleaned file saved as: {cleaned_file_path}")

#Run the checkDelistings.py file and Generate the report-symbol_status.csv File





































# Step 11: Insert Data into PostgreSQL
# Set up database connection using environment variables
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Create SQLAlchemy engine for database connection
engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# Insert data into the database
try:
    with engine.connect() as connection:
        data.to_sql('asset_ledger', con=connection, if_exists='append', index=False)
    print("Data successfully inserted into the database.")
except Exception as e:
    print(f"An error occurred during data insertion: {e}")
