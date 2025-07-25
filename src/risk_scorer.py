"""
Wallet Risk Scorer
Combines multiple risk features into a single risk score (0-1000)
"""

from typing import Dict
from config.config import RISK_WEIGHTS, DEFAULT_RISK_SCORE

class WalletRiskScorer:
    """Calculates comprehensive risk scores for wallet addresses."""
    
    def __init__(self):
        self.risk_weights = RISK_WEIGHTS
        self.validate_weights()
    
    def validate_weights(self):
        """Ensure risk weights sum to 1.0."""
        total_weight = sum(self.risk_weights.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Risk weights must sum to 1.0, got {total_weight}")
    
    def calculate_risk_score(self, features: Dict) -> int:
        """Calculate the overall risk score for a wallet."""
        try:
            # Extract individual risk components
            liquidation_risk = self._get_liquidation_risk_score(features)
            leverage_risk = self._get_leverage_risk_score(features)
            volatility_risk = self._get_volatility_risk_score(features)
            activity_risk = self._get_activity_risk_score(features)
            concentration_risk = self._get_concentration_risk_score(features)
            protocol_risk = self._get_protocol_risk_score(features)
            
            # Calculate weighted risk score
            weighted_score = (
                liquidation_risk * self.risk_weights['liquidation_risk'] +
                leverage_risk * self.risk_weights['leverage_risk'] +
                volatility_risk * self.risk_weights['volatility_risk'] +
                activity_risk * self.risk_weights['activity_risk'] +
                concentration_risk * self.risk_weights['concentration_risk'] +
                protocol_risk * self.risk_weights['protocol_risk']
            )
            
            # Convert to 0-1000 scale
            final_score = int(weighted_score * 1000)
            
            # Ensure score is within bounds
            final_score = max(0, min(1000, final_score))
            
            # Store component scores for analysis
            features['risk_components'] = {
                'liquidation_risk': liquidation_risk,
                'leverage_risk': leverage_risk,
                'volatility_risk': volatility_risk,
                'activity_risk': activity_risk,
                'concentration_risk': concentration_risk,
                'protocol_risk': protocol_risk,
                'weighted_score': weighted_score,
                'final_score': final_score
            }
            
            return final_score
            
        except Exception as e:
            print(f"Error calculating risk score: {e}")
            return DEFAULT_RISK_SCORE
    
    def _get_liquidation_risk_score(self, features: Dict) -> float:
        """Calculate liquidation risk component (0.0 - 1.0)."""
        health_factor_risk = features.get('health_factor_risk', 0.1)
        liquidation_risk = features.get('liquidation_risk', 0.0)
        
        # Weight health factor more heavily as it's the primary liquidation indicator
        liquidation_score = (health_factor_risk * 0.8 + liquidation_risk * 0.2)
        
        return min(liquidation_score, 1.0)
    
    def _get_leverage_risk_score(self, features: Dict) -> float:
        """Calculate leverage risk component (0.0 - 1.0)."""
        leverage_risk = features.get('leverage_risk', 0.1)
        leverage_ratio = features.get('leverage_ratio', 0.0)
        
        # Additional penalty for very high leverage
        if leverage_ratio > 0.9:
            leverage_penalty = 0.2
        elif leverage_ratio > 0.8:
            leverage_penalty = 0.1
        else:
            leverage_penalty = 0.0
        
        leverage_score = leverage_risk + leverage_penalty
        
        return min(leverage_score, 1.0)
    
    def _get_volatility_risk_score(self, features: Dict) -> float:
        """Calculate volatility risk component (0.0 - 1.0)."""
        volatility_risk = features.get('volatility_risk', 0.1)
        amount_volatility = features.get('amount_volatility', 0.1)
        transaction_volatility = features.get('transaction_volatility', 0.1)
        
        # Combine different volatility measures
        combined_volatility = (volatility_risk * 0.5 + 
                             amount_volatility * 0.3 + 
                             transaction_volatility * 0.2)
        
        return min(combined_volatility, 1.0)
    
    def _get_activity_risk_score(self, features: Dict) -> float:
        """Calculate activity risk component (0.0 - 1.0)."""
        activity_risk = features.get('activity_risk', 0.1)
        transaction_count = features.get('transaction_count', 0)
        
        # Adjust for extreme transaction counts
        if transaction_count == 0:
            # No activity is somewhat risky (no data)
            count_risk = 0.3
        elif transaction_count < 5:
            # Very low activity
            count_risk = 0.2
        elif transaction_count > 1000:
            # Extremely high activity (possible bot)
            count_risk = 0.7
        elif transaction_count > 500:
            # Very high activity
            count_risk = 0.4
        else:
            # Normal activity range
            count_risk = 0.1
        
        # Combine activity pattern risk with transaction count risk
        combined_activity = (activity_risk * 0.7 + count_risk * 0.3)
        
        return min(combined_activity, 1.0)
    
    def _get_concentration_risk_score(self, features: Dict) -> float:
        """Calculate concentration risk component (0.0 - 1.0)."""
        concentration_risk = features.get('concentration_risk', 0.1)
        asset_count = features.get('asset_count', 1)
        
        # Additional penalty for very low diversification
        if asset_count == 1:
            diversification_penalty = 0.3
        elif asset_count == 2:
            diversification_penalty = 0.1
        else:
            diversification_penalty = 0.0
        
        concentration_score = concentration_risk + diversification_penalty
        
        return min(concentration_score, 1.0)
    
    def _get_protocol_risk_score(self, features: Dict) -> float:
        """Calculate protocol interaction risk component (0.0 - 1.0)."""
        protocol_risk = features.get('protocol_risk', 0.1)
        gas_price_risk = features.get('gas_price_risk', 0.1)
        failure_rate = features.get('failure_rate', 0.0)
        liquidator_count = features.get('liquidator_count', 0)
        
        # Weight different protocol risk factors
        protocol_score = (
            protocol_risk * 0.4 +
            gas_price_risk * 0.3 +
            min(failure_rate * 2, 1.0) * 0.2 +  # Scale failure rate
            min(liquidator_count * 0.1, 0.3) * 0.1  # Cap liquidator impact
        )
        
        return min(protocol_score, 1.0)
    
    def get_risk_level_description(self, score: int) -> str:
        """Get human-readable risk level description."""
        if score <= 200:
            return "Low Risk - Conservative, well-collateralized positions"
        elif score <= 400:
            return "Medium-Low Risk - Generally stable with minor risk factors"
        elif score <= 600:
            return "Medium Risk - Some risk factors present, monitor closely"
        elif score <= 800:
            return "High Risk - Multiple risk indicators, increased attention needed"
        else:
            return "Very High Risk - Critical risk factors, immediate review required"
    
    def get_risk_recommendations(self, features: Dict, score: int) -> list[str]:
        """Generate risk-based recommendations."""
        recommendations = []
        
        # Get risk components
        components = features.get('risk_components', {})
        
        # Health factor recommendations
        health_factor = features.get('health_factor', 5.0)
        if health_factor < 1.5:
            recommendations.append("CRITICAL: Health factor below 1.5 - Consider reducing debt or adding collateral")
        elif health_factor < 2.0:
            recommendations.append("WARNING: Health factor below 2.0 - Monitor position closely")
        
        # Leverage recommendations
        leverage_ratio = features.get('leverage_ratio', 0.0)
        if leverage_ratio > 0.8:
            recommendations.append("High leverage detected - Consider reducing borrowed amounts")
        
        # Volatility recommendations
        volatility_risk = components.get('volatility_risk', 0.0)
        if volatility_risk > 0.6:
            recommendations.append("High transaction volatility - Review trading strategy")
        
        # Activity recommendations
        transaction_count = features.get('transaction_count', 0)
        if transaction_count > 500:
            recommendations.append("Very high activity detected - Verify automated strategies")
        elif transaction_count == 0:
            recommendations.append("No Compound transactions found - Score based on default assumptions")
        
        # Concentration recommendations
        asset_count = features.get('asset_count', 1)
        if asset_count <= 2:
            recommendations.append("Low asset diversification - Consider spreading risk across more assets")
        
        # Protocol recommendations
        failure_rate = features.get('failure_rate', 0.0)
        if failure_rate > 0.1:
            recommendations.append("High transaction failure rate detected - Review transaction patterns")
        
        liquidation_count = features.get('liquidation_count', 0)
        if liquidation_count > 0:
            recommendations.append(f"Previous liquidations detected ({liquidation_count}) - Exercise extra caution")
        
        # General score-based recommendations
        if score > 800:
            recommendations.append("URGENT: Very high risk score - Immediate portfolio review recommended")
        elif score > 600:
            recommendations.append("High risk score - Enhanced monitoring and risk management advised")
        elif score < 200:
            recommendations.append("Low risk profile - Continue current conservative approach")
        
        return recommendations
    
    def explain_score(self, features: Dict, score: int) -> Dict:
        """Provide detailed explanation of the risk score."""
        components = features.get('risk_components', {})
        
        explanation = {
            'total_score': score,
            'risk_level': self.get_risk_level_description(score),
            'component_breakdown': {
                'liquidation_risk': {
                    'score': round(components.get('liquidation_risk', 0) * 1000),
                    'weight': self.risk_weights['liquidation_risk'],
                    'contribution': round(components.get('liquidation_risk', 0) * self.risk_weights['liquidation_risk'] * 1000),
                    'description': 'Risk of position liquidation based on health factor'
                },
                'leverage_risk': {
                    'score': round(components.get('leverage_risk', 0) * 1000),
                    'weight': self.risk_weights['leverage_risk'],
                    'contribution': round(components.get('leverage_risk', 0) * self.risk_weights['leverage_risk'] * 1000),
                    'description': 'Risk from high debt-to-collateral ratios'
                },
                'volatility_risk': {
                    'score': round(components.get('volatility_risk', 0) * 1000),
                    'weight': self.risk_weights['volatility_risk'],
                    'contribution': round(components.get('volatility_risk', 0) * self.risk_weights['volatility_risk'] * 1000),
                    'description': 'Risk from erratic transaction patterns'
                },
                'activity_risk': {
                    'score': round(components.get('activity_risk', 0) * 1000),
                    'weight': self.risk_weights['activity_risk'],
                    'contribution': round(components.get('activity_risk', 0) * self.risk_weights['activity_risk'] * 1000),
                    'description': 'Risk from unusual activity patterns'
                },
                'concentration_risk': {
                    'score': round(components.get('concentration_risk', 0) * 1000),
                    'weight': self.risk_weights['concentration_risk'],
                    'contribution': round(components.get('concentration_risk', 0) * self.risk_weights['concentration_risk'] * 1000),
                    'description': 'Risk from lack of asset diversification'
                },
                'protocol_risk': {
                    'score': round(components.get('protocol_risk', 0) * 1000),
                    'weight': self.risk_weights['protocol_risk'],
                    'contribution': round(components.get('protocol_risk', 0) * self.risk_weights['protocol_risk'] * 1000),
                    'description': 'Risk from protocol interaction patterns'
                }
            },
            'key_metrics': {
                'health_factor': features.get('health_factor', 'N/A'),
                'leverage_ratio': round(features.get('leverage_ratio', 0), 3),
                'transaction_count': features.get('transaction_count', 0),
                'liquidation_count': features.get('liquidation_count', 0)
            },
            'recommendations': self.get_risk_recommendations(features, score)
        }
        
        return explanation