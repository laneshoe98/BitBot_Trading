CREATE TABLE russel_3000 (
    ticker VARCHAR(255) PRIMARY KEY,
    company_name TEXT,
    sector JSONB,
    industry JSONB,
    current_price NUMERIC,
    initial_investment NUMERIC,
    total_return_dollars NUMERIC,
    total_return_percent NUMERIC,
    fundamentals JSONB,
    price_action JSONB,
    purchase_history JSONB,
    market_cap_history JSONB,
    last_updated TIMESTAMP WITH TIME ZONE
);

CREATE TABLE asset_ledger (
    transaction_id SERIAL PRIMARY KEY,
    ticker VARCHAR(255) REFERENCES russel_3000(ticker),
    asset_name VARCHAR(250),
    quantity DECIMAL(10,2),
    price DECIMAL(10,2),
    transaction_amount DECIMAL(10,2),
    commission DECIMAL(10,2),
    fees DECIMAL(10,2),
    portfolio_name VARCHAR(250),
    transaction_date DATE,
    notes TEXT
);

CREATE TABLE portfolios (
    portfolio_id INT PRIMARY KEY,
    portfolio_name VARCHAR(50) NOT NULL,
    total_asset_value DECIMAL(10,2) NOT NULL
);

CREATE TABLE my_assets (
    asset_id SERIAL PRIMARY KEY,
    asset_name VARCHAR(45) NOT NULL,
    ticker VARCHAR(45) DEFAULT NULL,
    current_price DECIMAL(10,0) NOT NULL,
    total_quantity INT NOT NULL,
    transaction_id INT NOT NULL REFERENCES asset_ledger(transaction_id),
    UNIQUE (asset_id),
    UNIQUE (asset_name)
);