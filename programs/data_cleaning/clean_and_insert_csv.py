import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import json

# Load environment variables from the .env file
load_dotenv(r'X:\path\to\your\external\SSD\server_credentials.env')  # Replace with actual path

# Database connection details
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

try:
    # Connect to the PostgreSQL database
    connection = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = connection.cursor()

    # Load and clean the data as before
    file_path = r'C:\Users\Lane\Downloads\Accounts_History_2021.csv'  # Update this path as needed
    data = pd.read_csv(file_path)

    # Clean data (Steps 1 to 8 from previous code)

    # Step 9: Insert cleaned data into asset_ledger
    for _, row in data.iterrows():
        cursor.execute("""
            INSERT INTO asset_ledger (ticker, asset_name, quantity, price, transaction_amount, commission, fees, portfolio_name, transaction_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['ticker'], row['asset_name'], row['quantity'], row['price'], row['transaction_amount'], 
            row['commission'], row['fees'], row['portfolio_name'], row['transaction_date'], row['notes']
        ))

    # Commit the transaction to save data in asset_ledger
    connection.commit()
    print("Data successfully inserted into asset_ledger.")

    # Step 10: Update russel_3000 table with purchase history
    for _, row in data.iterrows():
        # Create a JSON entry for this transaction
        transaction = {
            "transaction_date": row['transaction_date'],
            "quantity": row['quantity'],
            "price": row['price'],
            "transaction_amount": row['transaction_amount'],
            "commission": row['commission'],
            "fees": row['fees'],
            "notes": row['notes']
        }

        # Check if ticker exists in russel_3000
        cursor.execute("SELECT purchase_history FROM russel_3000 WHERE ticker = %s", (row['ticker'],))
        result = cursor.fetchone()

        if result is None:
            # If ticker does not exist, insert it with this transaction as the initial purchase history
            purchase_history = [transaction]
            cursor.execute("""
                INSERT INTO russel_3000 (ticker, company_name, purchase_history) 
                VALUES (%s, %s, %s)
            """, (row['ticker'], row['asset_name'], json.dumps(purchase_history)))
        else:
            # If ticker exists, append this transaction to purchase_history
            purchase_history = json.loads(result[0]) if result[0] else []
            purchase_history.append(transaction)
            cursor.execute("""
                UPDATE russel_3000
                SET purchase_history = %s
                WHERE ticker = %s
            """, (json.dumps(purchase_history), row['ticker']))

    # Commit the transaction to save updates in russel_3000
    connection.commit()
    print("russel_3000 table updated with purchase history.")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the cursor and connection if they were created
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()
