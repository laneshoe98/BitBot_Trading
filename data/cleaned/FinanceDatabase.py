import financedatabase as fd
import pandas as pd
import csv

# Initialize the Equities database
equities = fd.Equities()

# Retrieve data for a specific country or sector (without market cap or exchange filtering)
data = equities.select(country="United States")  # Add sector or industry if desired
print(data)

data.to_csv("equities_data5.csv", index=False)
print("data saved as file")