"""
API key management for the DeFi Wallet Risk Scoring System
"""

import os

# Load Etherscan API key from environment variable
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
if not ETHERSCAN_API_KEY:
    raise ValueError("ETHERSCAN_API_KEY environment variable not set")

# Placeholder for future API keys (e.g., Infura, Alchemy, or other services)
# INFURA_API_KEY = os.getenv('INFURA_API_KEY')
# ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY')