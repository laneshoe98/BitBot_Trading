import pandas as pd
import json
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(r'C:\Users\Lane\Documents\Projects\trading_bot\server_credentials.env')

# Database credentials from environment variables
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Load master_data9.csv as a DataFrame
file_path = r'C:\Users\Lane\Documents\Projects\trading_bot\data\master_data9_copy.csv'  # Update with the actual path
data = pd.read_csv(file_path)

# Convert 'sector' and 'industry' columns to JSON arrays with one element for now
data['sector'] = data['sector'].apply(lambda x: json.dumps([x]) if pd.notna(x) else json.dumps([]))
data['industry'] = data['industry'].apply(lambda x: json.dumps([x]) if pd.notna(x) else json.dumps([]))

# Create SQLAlchemy engine for PostgreSQL connection
engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# Insert data into tracked_companies
try:
    with engine.connect() as connection:
        data.to_sql('tracked_companies', con=connection, if_exists='append', index=False)
    print("Data from master_data9.csv successfully inserted into tracked_companies.")
except Exception as e:
    print(f"An error occurred during data insertion: {e}")
