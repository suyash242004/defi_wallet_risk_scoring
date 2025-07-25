"""
Configuration settings for the DeFi Wallet Risk Scoring System
"""

# Risk factor weights (must sum to 1.0)
RISK_WEIGHTS = {
    'liquidation_risk': 0.25,  # Health factor and liquidation history
    'leverage_risk': 0.20,     # Debt-to-collateral ratios
    'volatility_risk': 0.20,   # Transaction pattern volatility
    'activity_risk': 0.15,     # Activity frequency and diversity
    'concentration_risk': 0.10, # Asset concentration
    'protocol_risk': 0.10      # Protocol interaction patterns
}

# API Configuration
API_RATE_LIMIT = 2  # Requests per second for Etherscan API (5 request rate limit)
MAX_RETRIES = 3     # Maximum retry attempts for failed requests
REQUEST_TIMEOUT = 30 # Request timeout in seconds
BATCH_SIZE = 10     # Number of wallets to process in parallel

# Default values
DEFAULT_RISK_SCORE = 350  # Default score for wallets with insufficient data
MIN_TRANSACTIONS_FOR_ANALYSIS = 1  # Minimum transactions needed for full analysis

# Score thresholds for risk levels
RISK_THRESHOLDS = {
    'low': 200,
    'medium_low': 400,
    'medium': 600,
    'high': 800,
    'very_high': 1000
}

# Health factor thresholds
HEALTH_FACTOR_THRESHOLDS = {
    'critical': 1.0,
    'very_high_risk': 1.2,
    'high_risk': 1.5,
    'medium_risk': 2.0,
    'low_risk': float('inf')
}

# Leverage ratio thresholds
LEVERAGE_THRESHOLDS = {
    'low': 0.3,
    'medium': 0.5,
    'high': 0.7,
    'very_high': 0.8,
    'extreme': 1.0
}

# Gas price thresholds (in Gwei)
GAS_PRICE_THRESHOLDS = {
    'normal': 20,
    'high': 50,
    'extreme': 100
}

# Activity frequency thresholds (in days)
ACTIVITY_FREQUENCY_THRESHOLDS = {
    'very_frequent': 1,    # More than once per day
    'frequent': 7,         # More than once per week
    'normal': 30,          # More than once per month
    'infrequent': 90,      # More than once per quarter
    'very_infrequent': float('inf')  # Less frequent than quarterly
}

# Concentration thresholds (Herfindahl-Hirschman Index)
CONCENTRATION_THRESHOLDS = {
    'well_diversified': 0.3,
    'moderately_diversified': 0.5,
    'somewhat_concentrated': 0.7,
    'highly_concentrated': 1.0
}

# Logging configuration
LOG_LEVEL = 'INFO'  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = 'logs/risk_scoring.log'  # Path for log file

# Data storage paths
RAW_DATA_PATH = 'data/raw'
OUTPUT_PATH = 'output'
INPUT_WALLET_FILE = 'data/input/wallet_addresses.csv'