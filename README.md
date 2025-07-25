# DeFi Wallet Risk Scoring System

A comprehensive risk assessment tool for analyzing wallet addresses interacting with Compound V2/V3 protocols.

## Project Overview

This system analyzes wallet transaction patterns on Compound protocol to assign risk scores from 0-1000 based on multiple risk factors including liquidation risk, leverage, volatility, and activity patterns.

## Features

- **Real-time Data Fetching**: Uses Etherscan API and Compound subgraphs
- **Multi-factor Risk Analysis**: 6 key risk indicators with weighted scoring
- **Scalable Architecture**: Batch processing for multiple wallets
- **Comprehensive Reporting**: Detailed scoring methodology and results

## File Structure

```
defi-wallet-risk-scoring/
├── src/
│   ├── data_collector.py          # API integrations and data fetching
│   ├── feature_extractor.py       # Feature engineering and calculations
│   ├── risk_scorer.py            # Risk scoring algorithm
│   └── main.py                   # Main execution script
├── config/
│   ├── config.py                 # Configuration settings
│   └── api_keys.py              # API key management
├── data/
│   ├── input/
│   │   └── wallet_addresses.csv  # Input wallet addresses
│   └── raw/                      # Raw transaction data
├── output/
│   ├── wallet_risk_scores.csv    # Final risk scores
│   └── detailed_analysis.json    # Detailed feature analysis
├── docs/
│   └── methodology.md            # Detailed methodology documentation
├── requirements.txt              # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Prerequisites

- Python 3.8 or higher
- Etherscan API key (free tier available)
- Internet connection for API calls

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/defi-wallet-risk-scoring.git
   cd defi-wallet-risk-scoring
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Configure API keys:**
   - Get a free Etherscan API key from https://etherscan.io/apis
   - Add it to your `.env` file:
   ```
   ETHERSCAN_API_KEY=your_api_key_here
   ```

## Quick Start

1. **Prepare your wallet addresses:**

   - Place wallet addresses in `data/input/wallet_addresses.csv`
   - Format: One column named `wallet_id` with addresses

2. **Run the analysis:**

   ```bash
   python src/main.py
   ```

3. **Check results:**
   - Risk scores: `output/wallet_risk_scores.csv`
   - Detailed analysis: `output/detailed_analysis.json`

## API Integration

### Etherscan API

- **Purpose**: Fetch transaction history and current balances
- **Rate Limit**: 5 calls/second (free tier)
- **Endpoints Used**:
  - `api.etherscan.io/api?module=account&action=txlist`
  - `api.etherscan.io/api?module=account&action=tokentx`

### The Graph Protocol

- **Purpose**: Compound protocol-specific data
- **Endpoint**: `https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v2`
- **No API key required**

## Risk Scoring Methodology

### Core Risk Factors (Weighted):

1. **Liquidation Risk (25%)**

   - Health factor analysis
   - Collateralization ratios
   - Current position safety

2. **Leverage Risk (20%)**

   - Debt-to-collateral ratios
   - Maximum leverage used
   - Leverage consistency

3. **Volatility Risk (20%)**

   - Transaction amount variance
   - Frequency irregularities
   - Pattern deviations

4. **Activity Risk (15%)**

   - Transaction frequency
   - Action type diversity
   - Temporal patterns

5. **Concentration Risk (10%)**

   - Asset diversification
   - Single-asset exposure
   - Portfolio balance

6. **Protocol Risk (10%)**
   - Liquidation history
   - Gas usage patterns
   - Emergency behaviors

### Score Interpretation:

- **0-200**: Low Risk (Conservative, well-collateralized)
- **201-400**: Medium-Low Risk (Generally stable)
- **401-600**: Medium Risk (Some risk factors present)
- **601-800**: High Risk (Multiple risk indicators)
- **801-1000**: Very High Risk (High probability of issues)

## Configuration

Edit `config/config.py` to customize:

```python
# Risk factor weights (must sum to 1.0)
RISK_WEIGHTS = {
    'liquidation_risk': 0.25,
    'leverage_risk': 0.20,
    'volatility_risk': 0.20,
    'activity_risk': 0.15,
    'concentration_risk': 0.10,
    'protocol_risk': 0.10
}

# API settings
API_RATE_LIMIT = 5  # calls per second
MAX_RETRIES = 3
BATCH_SIZE = 10
```

## Example Usage

```python
from src.risk_scorer import WalletRiskScorer

# Initialize the scorer
scorer = WalletRiskScorer()

# Score a single wallet
wallet_address = "0x742d35Cc6634C0532925a3b8D45e3a8d83c5CC06"
risk_score = scorer.score_wallet(wallet_address)
print(f"Risk Score: {risk_score}")

# Batch process multiple wallets
wallet_list = ["0x742d35Cc...", "0x123abc..."]
scores = scorer.batch_score(wallet_list)
```

## Output Format

### wallet_risk_scores.csv

```csv
wallet_id,score
0x742d35Cc6634C0532925a3b8D45e3a8d83c5CC06,347
0x123abc...,692
```

### detailed_analysis.json

```json
{
  "0x742d35Cc...": {
    "total_score": 347,
    "risk_factors": {
      "liquidation_risk": 0.15,
      "leverage_risk": 0.22,
      "volatility_risk": 0.18,
      "activity_risk": 0.12,
      "concentration_risk": 0.08,
      "protocol_risk": 0.05
    },
    "health_factor": 2.3,
    "total_borrowed": 15000,
    "total_supplied": 50000
  }
}
```

## Error Handling

The system includes robust error handling for:

- API rate limiting (automatic retries with exponential backoff)
- Network timeouts
- Invalid wallet addresses
- Missing transaction data
- Malformed API responses

## Performance Optimization

- **Caching**: API responses cached locally to avoid repeated calls
- **Batch Processing**: Multiple wallets processed efficiently
- **Parallel Execution**: Multi-threaded API calls (respecting rate limits)
- **Data Persistence**: Intermediate results saved for recovery

## Troubleshooting

**Common Issues:**

1. **API Rate Limiting**

   - Solution: Reduce `API_RATE_LIMIT` in config
   - Check your API key limits

2. **No Transaction Data**

   - Some wallets may not have Compound interactions
   - System assigns default low-risk score

3. **Network Errors**

   - System automatically retries failed requests
   - Check internet connection

4. **Invalid Wallet Addresses**
   - System validates addresses before processing
   - Invalid addresses are logged and skipped

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:

- Create an issue on GitHub
- Check the documentation in `docs/methodology.md`
- Review the troubleshooting section above

## Disclaimer

This tool is for educational and research purposes. Always conduct your own due diligence before making financial decisions. The risk scores are estimates based on historical data and may not predict future performance.
