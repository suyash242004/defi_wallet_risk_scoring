"""
Risk Feature Extractor
Calculates various risk metrics from transaction data
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, Counter
import statistics

class RiskFeatureExtractor:
    """Extracts risk-related features from wallet transaction data."""
    
    def __init__(self):
        self.current_timestamp = datetime.now()
    
    def extract_features(self, wallet_address: str, transaction_data: Dict) -> Dict:
        """Extract all risk features for a wallet."""
        
        features = {
            'wallet_address': wallet_address,
            'extraction_timestamp': self.current_timestamp.isoformat()
        }
        
        # Extract different categories of features
        features.update(self._extract_liquidation_features(transaction_data))
        features.update(self._extract_leverage_features(transaction_data))
        features.update(self._extract_volatility_features(transaction_data))
        features.update(self._extract_activity_features(transaction_data))
        features.update(self._extract_concentration_features(transaction_data))
        features.update(self._extract_protocol_features(transaction_data))
        
        return features
    
    def _extract_liquidation_features(self, data: Dict) -> Dict:
        """Extract features related to liquidation risk."""
        features = {}
        
        # Calculate health factor from compound data
        compound_data = data.get('compound_data', {})
        account_data = compound_data.get('account')
        
        if account_data and account_data.get('tokens'):
            health_factor = self._calculate_health_factor(account_data)
            features['health_factor'] = health_factor
            
            # Health factor risk score (inverse relationship)
            if health_factor >= 2.0:
                features['health_factor_risk'] = 0.1
            elif health_factor >= 1.5:
                features['health_factor_risk'] = 0.3
            elif health_factor >= 1.2:
                features['health_factor_risk'] = 0.6
            elif health_factor >= 1.0:
                features['health_factor_risk'] = 0.9
            else:
                features['health_factor_risk'] = 1.0
        else:
            features['health_factor'] = 5.0  # Default safe value
            features['health_factor_risk'] = 0.1
        
        # Liquidation history
        liquidation_count = 0
        if account_data:
            liquidation_count = int(account_data.get('countLiquidated', 0))
        
        features['liquidation_count'] = liquidation_count
        features['liquidation_risk'] = min(liquidation_count * 0.2, 1.0)
        
        return features
    
    def _calculate_health_factor(self, account_data: Dict) -> float:
        """Calculate health factor from account data."""
        total_collateral_usd = 0
        total_borrow_usd = 0
        
        for token in account_data.get('tokens', []):
            supplied = float(token.get('totalUnderlyingSupplied', 0))
            borrowed = float(token.get('totalUnderlyingBorrowed', 0))
            
            # Simplified calculation with assumed prices and collateral factors
            # In production, would use real-time prices and market data
            collateral_factor = 0.75  # Typical collateral factor
            
            total_collateral_usd += supplied * collateral_factor
            total_borrow_usd += borrowed
        
        if total_borrow_usd == 0:
            return 5.0  # No debt = very healthy
        
        return total_collateral_usd / total_borrow_usd
    
    def _extract_leverage_features(self, data: Dict) -> Dict:
        """Extract features related to leverage usage."""
        features = {}
        
        compound_data = data.get('compound_data', {})
        account_data = compound_data.get('account')
        
        total_supplied = 0
        total_borrowed = 0
        
        if account_data and account_data.get('tokens'):
            for token in account_data['tokens']:
                supplied = float(token.get('totalUnderlyingSupplied', 0))
                borrowed = float(token.get('totalUnderlyingBorrowed', 0))
                
                total_supplied += supplied
                total_borrowed += borrowed
        
        features['total_supplied'] = total_supplied
        features['total_borrowed'] = total_borrowed
        
        # Calculate leverage ratio
        if total_supplied > 0:
            leverage_ratio = total_borrowed / total_supplied
        else:
            leverage_ratio = 0
        
        features['leverage_ratio'] = leverage_ratio
        
        # Leverage risk score
        if leverage_ratio <= 0.3:
            features['leverage_risk'] = 0.1
        elif leverage_ratio <= 0.5:
            features['leverage_risk'] = 0.3
        elif leverage_ratio <= 0.7:
            features['leverage_risk'] = 0.6
        elif leverage_ratio <= 0.8:
            features['leverage_risk'] = 0.8
        else:
            features['leverage_risk'] = 1.0
        
        return features
    
    def _extract_volatility_features(self, data: Dict) -> Dict:
        """Extract features related to transaction volatility."""
        features = {}
        
        compound_txs = data.get('compound_transactions', [])
        
        if not compound_txs:
            features['transaction_volatility'] = 0.1
            features['amount_volatility'] = 0.1
            features['volatility_risk'] = 0.1
            return features
        
        # Analyze transaction amounts
        amounts = []
        for tx in compound_txs:
            try:
                amount = float(tx.get('value', 0)) / 10**18  # Convert from wei
                if amount > 0:
                    amounts.append(amount)
            except (ValueError, TypeError):
                continue
        
        if len(amounts) < 2:
            features['transaction_volatility'] = 0.1
            features['amount_volatility'] = 0.1
            features['volatility_risk'] = 0.1
            return features
        
        # Calculate coefficient of variation
        mean_amount = statistics.mean(amounts)
        std_amount = statistics.stdev(amounts)
        
        if mean_amount > 0:
            cv = std_amount / mean_amount
        else:
            cv = 0
        
        features['amount_mean'] = mean_amount
        features['amount_std'] = std_amount
        features['amount_volatility'] = min(cv, 2.0)  # Cap at 2.0
        
        # Transaction frequency volatility
        timestamps = []
        for tx in compound_txs:
            try:
                timestamp = int(tx.get('timeStamp', 0))
                timestamps.append(timestamp)
            except (ValueError, TypeError):
                continue
        
        if len(timestamps) >= 2:
            timestamps.sort()
            intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            
            if intervals:
                mean_interval = statistics.mean(intervals)
                std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
                
                if mean_interval > 0:
                    interval_cv = std_interval / mean_interval
                else:
                    interval_cv = 0
                
                features['transaction_volatility'] = min(interval_cv, 2.0)
            else:
                features['transaction_volatility'] = 0.1
        else:
            features['transaction_volatility'] = 0.1
        
        # Combined volatility risk
        volatility_risk = (features['amount_volatility'] + features['transaction_volatility']) / 2
        features['volatility_risk'] = min(volatility_risk, 1.0)
        
        return features
    
    def _extract_activity_features(self, data: Dict) -> Dict:
        """Extract features related to activity patterns."""
        features = {}
        
        compound_txs = data.get('compound_transactions', [])
        
        if not compound_txs:
            features['transaction_count'] = 0
            features['activity_frequency'] = 0
            features['action_diversity'] = 0
            features['activity_risk'] = 0.1
            return features
        
        features['transaction_count'] = len(compound_txs)
        
        # Analyze transaction frequency
        timestamps = []
        for tx in compound_txs:
            try:
                timestamp = int(tx.get('timeStamp', 0))
                timestamps.append(timestamp)
            except (ValueError, TypeError):
                continue
        
        if len(timestamps) >= 2:
            timestamps.sort()
            time_span = timestamps[-1] - timestamps[0]
            avg_interval = time_span / (len(timestamps) - 1) if len(timestamps) > 1 else 0
            
            # Convert to days
            avg_interval_days = avg_interval / (24 * 3600)
            features['avg_transaction_interval_days'] = avg_interval_days
            
            # Frequency risk (very frequent or very infrequent is risky)
            if avg_interval_days < 1:  # More than once per day
                frequency_risk = 0.8
            elif avg_interval_days < 7:  # More than once per week
                frequency_risk = 0.3
            elif avg_interval_days < 30:  # More than once per month
                frequency_risk = 0.1
            elif avg_interval_days < 90:  # More than once per quarter
                frequency_risk = 0.2
            else:  # Very infrequent
                frequency_risk = 0.6
            
            features['activity_frequency'] = frequency_risk
        else:
            features['avg_transaction_interval_days'] = 0
            features['activity_frequency'] = 0.5
        
        # Action diversity (function calls)
        actions = []
        for tx in compound_txs:
            method_id = tx.get('methodId', '')
            if method_id:
                actions.append(method_id)
        
        unique_actions = len(set(actions))
        total_actions = len(actions)
        
        if total_actions > 0:
            action_diversity = unique_actions / total_actions
        else:
            action_diversity = 0
        
        features['action_diversity'] = action_diversity
        features['unique_actions'] = unique_actions
        
        # Activity risk (low diversity = higher risk)
        if action_diversity >= 0.5:
            diversity_risk = 0.1
        elif action_diversity >= 0.3:
            diversity_risk = 0.3
        elif action_diversity >= 0.2:
            diversity_risk = 0.6
        else:
            diversity_risk = 0.9
        
        # Combined activity risk
        activity_risk = (features['activity_frequency'] + diversity_risk) / 2
        features['activity_risk'] = activity_risk
        
        return features
    
    def _extract_concentration_features(self, data: Dict) -> Dict:
        """Extract features related to asset concentration."""
        features = {}
        
        compound_data = data.get('compound_data', {})
        account_data = compound_data.get('account')
        
        if not account_data or not account_data.get('tokens'):
            features['asset_concentration'] = 0.1
            features['concentration_risk'] = 0.1
            return features
        
        # Calculate Herfindahl-Hirschman Index for concentration
        total_value = 0
        asset_values = []
        
        for token in account_data['tokens']:
            supplied = float(token.get('totalUnderlyingSupplied', 0))
            borrowed = float(token.get('totalUnderlyingBorrowed', 0))
            net_value = supplied - borrowed
            
            if net_value > 0:
                asset_values.append(net_value)
                total_value += net_value
        
        if total_value == 0 or len(asset_values) == 0:
            features['asset_concentration'] = 0.1
            features['concentration_risk'] = 0.1
            return features
        
        # Calculate HHI
        hhi = sum((value / total_value) ** 2 for value in asset_values)
        
        features['asset_count'] = len(asset_values)
        features['asset_concentration'] = hhi
        
        # Concentration risk (higher HHI = more concentrated = higher risk)
        if hhi <= 0.3:  # Well diversified
            concentration_risk = 0.1
        elif hhi <= 0.5:  # Moderately diversified
            concentration_risk = 0.3
        elif hhi <= 0.7:  # Somewhat concentrated
            concentration_risk = 0.6
        else:  # Highly concentrated
            concentration_risk = 0.9
        
        features['concentration_risk'] = concentration_risk
        
        return features
    
    def _extract_protocol_features(self, data: Dict) -> Dict:
        """Extract features related to protocol interaction patterns."""
        features = {}
        
        compound_txs = data.get('compound_transactions', [])
        normal_txs = data.get('normal_transactions', [])
        
        # Gas usage analysis
        gas_prices = []
        gas_used_values = []
        
        for tx in normal_txs[:50]:  # Analyze recent 50 transactions
            try:
                gas_price = int(tx.get('gasPrice', 0))
                gas_used = int(tx.get('gasUsed', 0))
                
                if gas_price > 0:
                    gas_prices.append(gas_price / 10**9)  # Convert to Gwei
                if gas_used > 0:
                    gas_used_values.append(gas_used)
                    
            except (ValueError, TypeError):
                continue
        
        if gas_prices:
            avg_gas_price = statistics.mean(gas_prices)
            max_gas_price = max(gas_prices)
            
            features['avg_gas_price_gwei'] = avg_gas_price
            features['max_gas_price_gwei'] = max_gas_price
            
            # High gas price usage indicates urgency/desperation
            if max_gas_price > 100:  # Very high gas
                gas_risk = 0.8
            elif max_gas_price > 50:  # High gas
                gas_risk = 0.5
            elif max_gas_price > 20:  # Moderate gas
                gas_risk = 0.2
            else:
                gas_risk = 0.1
            
            features['gas_price_risk'] = gas_risk
        else:
            features['avg_gas_price_gwei'] = 0
            features['max_gas_price_gwei'] = 0
            features['gas_price_risk'] = 0.1
        
        # Failed transaction analysis
        failed_txs = [tx for tx in normal_txs if tx.get('isError') == '1']
        total_txs = len(normal_txs)
        
        if total_txs > 0:
            failure_rate = len(failed_txs) / total_txs
        else:
            failure_rate = 0
        
        features['failure_rate'] = failure_rate
        features['failed_transaction_count'] = len(failed_txs)
        
        # Liquidation involvement
        compound_data = data.get('compound_data', {})
        account_data = compound_data.get('account')
        
        liquidator_count = 0
        if account_data:
            liquidator_count = int(account_data.get('countLiquidator', 0))
        
        features['liquidator_count'] = liquidator_count
        
        # Protocol risk score
        protocol_risk_components = [
            features['gas_price_risk'],
            min(failure_rate * 2, 1.0),  # Scale failure rate
            min(liquidator_count * 0.1, 0.5)  # Liquidator activity
        ]
        
        features['protocol_risk'] = statistics.mean(protocol_risk_components)
        
        return features