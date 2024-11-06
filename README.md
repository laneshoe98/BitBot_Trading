#Data Science Process
[Fourth, format and split dream data into 3 sections
    Sections 1 and 2 are for training (80%)
    Section 3 is for testing (20%)
Fifth, run analytics on the data
    Supervised learning Techniques
        Continuous (Regression techniques)
            Start with linear Regression
            Move on to regularized regression
                Ridge Regression
                Lasso Regression
        Classification (Classification techniques)
            Start with Logistic Regression
            Move on to tree based models
                Random Forests
                Gradient Boosting
    Unsupervised learning Techniques
        Grouping Data Points (Clustering Technique)
            Start with K-Means Clustering
                Move on to Hierachical CLustering
                DBSCAN
                HMM? 
        Reducing Features (Dimensionality Reduction Technique)
            Start with Principlal Component Analysis (PCA)
                Move on to T-SNE for data visualization
                Or use Topic Modeling Techniques for text data
]


#Roadmap: Steps for Integration and Synchronization

[Step 1: Define and Set Up Table Relationships (Schema Design)
Goal: Ensure that each table is structured with unique identifiers (symbol or company_id), establishing foreign key relationships where needed.
Action: Confirm that tracked_companies and asset_ledger tables link by symbol (or another unique identifier).
Output: A reliable reference key structure that allows cross-table queries.

Step 2: Insert Data into asset_ledger Table (Initial Population)
Goal: Load initial buy and sell data into the asset_ledger table if it isn’t already populated.
Action: Use your existing code to populate this data table.
Output: asset_ledger contains accurate and complete transaction data for each symbol.

Step 3: Sync purchase_history JSONB in tracked_companies with asset_ledger
Goal: Consolidate transaction data from asset_ledger into the purchase_history JSONB column in tracked_companies.
Action:
Write a function that queries asset_ledger by symbol and compiles an array of buy and sell records.
Populate purchase_history in tracked_companies with a JSON structure, e.g., [{date: 'YYYY-MM-DD', type: 'buy/sell', amount: XX, price: YY}, ...].
Output: A JSONB object in each tracked_companies row containing a record of transactions.

Step 4: Calculate initial_investment in tracked_companies from purchase_history
Goal: Use purchase_history JSONB to calculate and populate the initial investment amount for each symbol.
Action:
Write a function that parses purchase_history for buy transactions and calculates initial_investment as the sum of all initial purchase values.
Insert this calculated value into the initial_investment column in tracked_companies.
Output: initial_investment populated with cumulative initial purchase values.

Step 5: Fetch current_price and market_cap_history from yfinance
Goal: Use yfinance to fetch and update current_price and market_cap_history.
Action:
Write a script that fetches current_price and market_cap for each symbol and updates tracked_companies.
For market_cap_history, store values as JSONB, structured by date, e.g., {"2023-01-01": 5000000000, ...}.
Output: current_price and market_cap_history populated in tracked_companies.

Step 6: Calculate total_return_dollars and total_return_percent in tracked_companies
Goal: Use purchase_history and current_price to calculate returns.
Action:
Calculate total_return_dollars as current_price * quantity_held - initial_investment.
Calculate total_return_percent as (total_return_dollars / initial_investment) * 100.
Populate tracked_companies with these values.
Output: total_return_dollars and total_return_percent columns filled out.

Step 7: Automatically Update last_updated with current_price Changes
Goal: Whenever current_price is updated, set last_updated to the current timestamp.
Action:
Add a line in your current_price update script to update last_updated with the timestamp.
Output: last_updated column reflects the most recent update for each company’s price.

Step 8: Populate price_action with Daily Candle Data
Goal: Populate price_action JSONB with daily OHLCV data for each symbol.
Action:
Write a yfinance script to fetch daily price data (OHLC and volume) and store it in price_action, structured by date (e.g., {"2023-01-01": {"open": XX, "high": YY, "low": ZZ, "close": AA, "volume": BB}}).
Use a chunked approach if needed, with one JSONB object per year.
Output: price_action column populated with historical daily data.

Step 9: Enhance price_action with High-Frequency Data for Selected Symbols
Goal: For high-priority stocks, supplement daily data with more granular (15-minute or 1-minute) data.
Action:
Modify the price_action fetching script to get high-frequency data for selected symbols.
Organize this data in the JSONB field by timestamp, e.g., {"2023-01-01 09:30": {"open": XX, "high": YY, "low": ZZ, "close": AA, "volume": BB}}.
Output: price_action contains granular data for selected stocks.

Step 10: Automate Updates and Run as a Routine Job
Goal: Regularly update current_price, market_cap_history, and recalculate values in tracked_companies to keep data fresh.
Action:
Set up a cron job or scheduling service to run Steps 5–7 periodically.
Output: Automatic updates for key fields in tracked_companies, keeping all data current.
]