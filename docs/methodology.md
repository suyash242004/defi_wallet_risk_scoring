# DeFi Wallet Risk Scoring Methodology

This document details the methodology used by the DeFi Wallet Risk Scoring System to assign risk scores (0–1000) to wallet addresses interacting with the Compound V2 protocol. The system evaluates risk based on transaction history and protocol-specific data, focusing on six key risk indicators: liquidation risk, leverage risk, volatility risk, activity risk, concentration risk, and protocol risk.

## 1. Data Collection Method

### Sources

The system collects data from two primary sources:

- **Etherscan API**: Provides transaction history, including normal transactions, internal transactions, ERC-20 token transactions, and current ETH balances. Endpoints include:
  - `api.etherscan.io/api?module=account&action=txlist` for normal transactions.
  - `api.etherscan.io/api?module=account&action=tokentx` for token transactions.
  - `api.etherscan.io/api?module=account&action=balance` for ETH balances.
  - Rate-limited to 5 calls/second (free tier), with exponential backoff for retries (`MAX_RETRIES=3`).
- **The Graph Protocol (Compound V2 Subgraph)**: Provides protocol-specific data, such as account details (e.g., `totalUnderlyingSupplied`, `totalUnderlyingBorrowed`, `countLiquidated`), via the endpoint `https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v2`. No API key is required.

### Process

1. **Wallet Address Input**: Wallet addresses are read from `data/input/wallet_addresses.csv`, containing a single column `wallet_id` with Ethereum addresses.
2. **Transaction Data Retrieval**:
   - Normal, internal, and token transactions are fetched for each wallet using Etherscan API.
   - Compound-specific transactions are filtered based on interactions with known Compound contract addresses (e.g., Comptroller, cETH, cDAI).
   - Compound account data (e.g., health factor, supplied/borrowed amounts) is retrieved from The Graph.
3. **Data Storage**: Raw transaction data is stored in `data/raw` for caching and recovery. Results are saved as `output/wallet_risk_scores.csv` (scores) and `output/detailed_analysis.json` (detailed features).

### Error Handling

- **API Failures**: Handled with retries (up to 3 attempts) and exponential backoff.
- **No Data**: Wallets with no transactions or Compound interactions receive a default risk score (`DEFAULT_RISK_SCORE=350`).
- **Invalid Addresses**: Skipped with error logging to `logs/risk_scoring.log`.

## 2. Feature Selection Rationale

The system extracts features from transaction and account data to capture risk-relevant behaviors. Features are grouped into six risk categories, selected based on their relevance to DeFi lending protocol risks, particularly for Compound V2.

### Liquidation Risk (25% weight)

- **Features**:
  - **Health Factor**: Ratio of collateral (adjusted by collateral factor) to borrowed amount. Lower health factors indicate higher liquidation risk.
  - **Liquidation Count**: Number of historical liquidations (`countLiquidated`).
- **Rationale**: Health factor is the primary indicator of liquidation risk in lending protocols. A health factor below 1.0 leads to liquidation, while values below 2.0 signal elevated risk. Past liquidations indicate a history of risky behavior.

### Leverage Risk (20% weight)

- **Features**:
  - **Leverage Ratio**: Total borrowed amount divided by total supplied amount.
  - **Total Supplied/Borrowed**: Absolute values of supplied and borrowed assets.
- **Rationale**: High leverage (debt-to-collateral ratio) increases exposure to price volatility and liquidation risk. Thresholds (e.g., 0.3, 0.5, 0.7, 0.8, 1.0) reflect increasing risk levels.

### Volatility Risk (20% weight)

- **Features**:
  - **Amount Volatility**: Coefficient of variation (CV) of transaction amounts.
  - **Transaction Volatility**: CV of time intervals between transactions.
- **Rationale**: Erratic transaction patterns (e.g., inconsistent amounts or timing) may indicate speculative or unstable behavior, increasing risk.

### Activity Risk (15% weight)

- **Features**:
  - **Transaction Count**: Total number of Compound transactions.
  - **Activity Frequency**: Average time between transactions (in days).
  - **Action Diversity**: Ratio of unique action types (method IDs) to total actions.
- **Rationale**: Very high or low transaction frequency and low action diversity can indicate risky behavior (e.g., bot activity or lack of engagement). Normal activity (weekly/monthly) is considered low risk.

### Concentration Risk (10% weight)

- **Features**:
  - **Asset Concentration**: Herfindahl-Hirschman Index (HHI) of net asset values.
  - **Asset Count**: Number of distinct assets in the portfolio.
- **Rationale**: High concentration in a single asset increases exposure to price volatility. HHI thresholds (0.3, 0.5, 0.7, 1.0) define diversification levels.

### Protocol Risk (10% weight)

- **Features**:
  - **Gas Price Risk**: Maximum and average gas prices used (in Gwei).
  - **Failure Rate**: Proportion of failed transactions.
  - **Liquidator Count**: Number of times the wallet acted as a liquidator.
- **Rationale**: High gas prices may indicate urgency (e.g., avoiding liquidation), while frequent transaction failures suggest operational issues. Liquidator activity is a minor risk factor but indicates protocol familiarity.

## 3. Scoring Method

### Feature Extraction

- **Process**: The `RiskFeatureExtractor` class processes raw transaction and account data to compute features for each risk category. Each feature is normalized to a 0.0–1.0 scale:
  - **Health Factor Risk**: Inversely mapped (e.g., health factor <1.0 → 1.0 risk, ≥2.0 → 0.1 risk).
  - **Leverage Risk**: Based on leverage ratio thresholds (e.g., >0.8 → 0.8–1.0 risk).
  - **Volatility Risk**: Combines CV of amounts and intervals, capped at 2.0.
  - **Activity Risk**: Combines frequency and diversity, with penalties for extreme transaction counts.
  - **Concentration Risk**: Based on HHI, with penalties for low asset counts.
  - **Protocol Risk**: Weighted average of gas price risk, failure rate, and liquidator activity.
- **Normalization**: All risk scores are capped at 1.0 to ensure consistency.

### Risk Score Calculation

- **Formula**: The `WalletRiskScorer` class computes a weighted sum of risk components:
  \[
  \text{Weighted Score} = \sum (\text{Risk Component} \times \text{Weight})
  \]
  where weights are defined in `config.py` (e.g., liquidation_risk: 0.25, leverage_risk: 0.20, etc.).
- **Scaling**: The weighted score (0.0–1.0) is multiplied by 1000 to produce a final score (0–1000).
- **Default Score**: If data is insufficient or an error occurs, the wallet is assigned `DEFAULT_RISK_SCORE=350`.

### Risk Level Interpretation

- **0–200**: Low Risk (conservative, well-collateralized).
- **201–400**: Medium-Low Risk (generally stable).
- **401–600**: Medium Risk (some risk factors present).
- **601–800**: High Risk (multiple risk indicators).
- **801–1000**: Very High Risk (critical risk factors).

## 4. Justification of Risk Indicators

### Liquidation Risk

- **Why Chosen**: Liquidation is the primary risk in lending protocols like Compound. A low health factor or history of liquidations directly correlates with financial distress.
- **Impact**: Given its critical nature, it has the highest weight (25%).

### Leverage Risk

- **Why Chosen**: High leverage amplifies losses during market downturns, increasing liquidation probability.
- **Impact**: Weighted at 20% due to its significant but secondary role compared to health factor.

### Volatility Risk

- **Why Chosen**: Inconsistent transaction patterns may reflect speculative or unstable strategies, which are risky in DeFi.
- **Impact**: Weighted at 20% to balance its importance with other financial metrics.

### Activity Risk

- **Why Chosen**: Unusual activity patterns (e.g., bot-like high frequency or no activity) can indicate operational or data-related risks.
- **Impact**: Weighted at 15% as it is less direct than financial metrics but still relevant.

### Concentration Risk

- **Why Chosen**: Lack of diversification increases exposure to single-asset price movements, a key risk in volatile crypto markets.
- **Impact**: Weighted at 10% as it is a secondary risk factor compared to leverage and liquidation.

### Protocol Risk

- **Why Chosen**: Interaction patterns (e.g., high gas prices, failed transactions) can indicate operational issues or risky behavior.
- **Impact**: Weighted at 10% as it complements other metrics but is less critical.

## 5. Scalability and Limitations

### Scalability

- **Batch Processing**: Supports processing multiple wallets (`BATCH_SIZE=10`) with rate limiting (`API_RATE_LIMIT=5`).
- **Caching**: Stores raw data in `data/raw` to avoid redundant API calls.
- **Parallel Execution**: Respects API limits while processing wallets efficiently.

### Limitations

- **Data Availability**: Relies on Etherscan and The Graph, which may have delays or incomplete data.
- **Price Data**: Uses simplified collateral factors (e.g., 0.75) instead of real-time prices, which may affect health factor accuracy.
- **Protocol Scope**: Limited to Compound V2; extending to V3 or other protocols requires additional data sources.

## 6. Output Format

- **wallet_risk_scores.csv**:
  ```csv
  wallet_id,score
  0x742d35Cc6634C0532925a3b8D45e3a8d83c5CC06,347
  ```
