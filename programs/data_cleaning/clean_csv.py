import pandas as pd
import os

# Load the CSV data
file_path = r'C:\Users\Lane\Downloads\Accounts_History (6).csv'  # Update this path as needed
data = pd.read_csv(file_path)

# Step 1: Remove any leading/trailing whitespace from all string columns
data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

# Step 2: Remove rows where 'ticker' is NaN to clean extraneous text
data = data.dropna(subset=['Symbol'])  # 'Symbol' is renamed to 'ticker' later in Step 2

# Step 3: Rename columns
rename_columns = {
    'Run Date': 'transaction_date',
    'Account': 'portfolio_name',
    'Action': 'notes',
    'Symbol': 'ticker',
    'Description': 'asset_name',
    'Quantity': 'quantity',
    'Price': 'price',
    'Amount': 'transaction_amount'
}
data = data.rename(columns=rename_columns)

# Step 4: Delete unnecessary columns
columns_to_delete = [
    'Type', 'Exchange Quantity', 'Exchange Currency', 'Currency', 
    'Exchange Rate', 'Accrued Interest', 'Settlement Date'
]
data = data.drop(columns=columns_to_delete, errors='ignore')

# Step 5: Add default columns for missing data
for col in ['commission', 'fees']:
    if col not in data.columns:
        data[col] = 0  # or use `pd.NA` for NaN if preferred

# Step 6: Reorder columns to match the specified order
final_columns_order = [
    'ticker', 'asset_name', 'quantity', 'price', 'transaction_amount', 
    'commission', 'fees', 'portfolio_name', 'transaction_date', 'notes'
]
data = data[final_columns_order]

# Step 7: Remove leading spaces from 'asset_name'
data['asset_name'] = data['asset_name'].str.lstrip()

# Step 8: Convert 'transaction_date' from MM/DD/YYYY to YYYY/MM/DD
data['transaction_date'] = pd.to_datetime(data['transaction_date'], format='%m/%d/%Y').dt.strftime('%Y/%m/%d')

# Step 9: Save to a new CSV file with '_cleaned' suffix
cleaned_file_path = os.path.splitext(file_path)[0] + '_cleaned.csv'
data.to_csv(cleaned_file_path, index=False)

print(f"Cleaned file saved as: {cleaned_file_path}")