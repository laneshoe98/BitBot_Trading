import pandas as pd
import yfinance as yf
import time

# Path to your master_data11.csv file
input_path = r'C:\Users\Lane\Documents\Projects\trading_bot\data\master_data11.csv'  # Update with the actual path to master_data11.csv
output_path = 'master_data12.csv'  # Save path for the updated file

# Load master_data11
master_data = pd.read_csv(input_path)

# Step 1: Filter to find rows with missing values in specific columns
columns_to_check = ['asset_name', 'sector', 'industry', 'first_traded']
rows_with_blanks = master_data[master_data[columns_to_check].isnull().any(axis=1)]

# Function to fetch data from yfinance and fill in only the blanks
def fetch_and_fill_data(row):
    symbol = row['symbol']
    
    try:
        # Fetch data from yfinance
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Fill only if the field is blank
        if pd.isna(row['asset_name']) or row['asset_name'] == '':
            row['asset_name'] = info.get('longName', '')
        if pd.isna(row['sector']) or row['sector'] == '':
            row['sector'] = info.get('sector', '')
        if pd.isna(row['industry']) or row['industry'] == '':
            row['industry'] = info.get('industry', '')
        
        # Attempt to get first traded date using history as a fallback
        if pd.isna(row['first_traded']) or row['first_traded'] == '':
            first_trade_date = info.get('firstTradeDate', None)
            if not first_trade_date:
                history_data = stock.history(period="max")
                first_trade_date = history_data.index.min().strftime('%Y-%m-%d') if not history_data.empty else ''
            row['first_traded'] = first_trade_date

    except Exception as e:
        print(f"Could not retrieve data for {symbol}: {e}")
    
    return row

# Step 2: Apply the function only to rows with missing values
updated_rows = rows_with_blanks.apply(fetch_and_fill_data, axis=1)

# Step 3: Update only the rows with new data back into the main DataFrame
master_data.update(updated_rows)

# Step 4: Save the filled data to a new CSV file
master_data.to_csv(output_path, index=False)

print(f"Data with blanks filled saved as {output_path}")