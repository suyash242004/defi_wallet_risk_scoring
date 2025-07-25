#!/usr/bin/env python3
"""
DeFi Wallet Risk Scoring System - Main Execution Script
Author: Suyash
Date: 24 July 2025

This script orchestrates the entire risk scoring process for wallet addresses
interacting with Compound V2/V3 protocols.
"""

import os
import sys
import time
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data_collector import CompoundDataCollector
from feature_extractor import RiskFeatureExtractor
from risk_scorer import WalletRiskScorer
# from config.config import *
# from config.config import API_RATE_LIMIT, MAX_RETRIES, REQUEST_TIMEOUT, BATCH_SIZE
from config.config import (
    API_RATE_LIMIT, MAX_RETRIES, REQUEST_TIMEOUT, BATCH_SIZE,
    DEFAULT_RISK_SCORE, MIN_TRANSACTIONS_FOR_ANALYSIS, RISK_WEIGHTS,
    LOG_LEVEL, LOG_FILE, RAW_DATA_PATH, OUTPUT_PATH, INPUT_WALLET_FILE
)

def setup_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        'data/raw',
        'output',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def load_wallet_addresses(file_path='data/input/wallet_addresses.csv'):
    """Load wallet addresses from CSV file."""
    try:
        df = pd.read_csv(file_path)
        if 'wallet_id' not in df.columns:
            raise ValueError("CSV must contain 'wallet_id' column")
            
        wallets = df['wallet_id'].tolist()
        print(f"✓ Loaded {len(wallets)} wallet addresses")
        return wallets
        
    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found")
        print("Please ensure wallet addresses are in data/input/wallet_addresses.csv")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading wallet addresses: {e}")
        sys.exit(1)

def save_results(scores, detailed_analysis):
    """Save results to output files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save risk scores CSV
    scores_df = pd.DataFrame([
        {'wallet_id': wallet, 'score': score}
        for wallet, score in scores.items()
    ])
    
    output_file = 'output/wallet_risk_scores.csv'
    scores_df.to_csv(output_file, index=False)
    print(f"✓ Risk scores saved to {output_file}")
    
    # Save detailed analysis JSON
    detailed_file = 'output/detailed_analysis.json'
    with open(detailed_file, 'w') as f:
        json.dump(detailed_analysis, f, indent=2, default=str)
    print(f"✓ Detailed analysis saved to {detailed_file}")
    
    # Create backup with timestamp
    backup_file = f'output/backup/scores_{timestamp}.csv'
    Path('output/backup').mkdir(exist_ok=True)
    scores_df.to_csv(backup_file, index=False)
    
    return output_file, detailed_file

def print_summary_statistics(scores):
    """Print summary statistics of the risk scores."""
    score_values = list(scores.values())
    
    print("\n" + "="*50)
    print("RISK SCORING SUMMARY")
    print("="*50)
    print(f"Total Wallets Analyzed: {len(score_values)}")
    print(f"Average Risk Score: {sum(score_values)/len(score_values):.1f}")
    print(f"Minimum Risk Score: {min(score_values)}")
    print(f"Maximum Risk Score: {max(score_values)}")
    
    # Risk distribution
    risk_buckets = {
        'Low Risk (0-200)': sum(1 for s in score_values if s <= 200),
        'Medium-Low Risk (201-400)': sum(1 for s in score_values if 201 <= s <= 400),
        'Medium Risk (401-600)': sum(1 for s in score_values if 401 <= s <= 600),
        'High Risk (601-800)': sum(1 for s in score_values if 601 <= s <= 800),
        'Very High Risk (801-1000)': sum(1 for s in score_values if s > 800)
    }
    
    print("\nRisk Distribution:")
    for risk_level, count in risk_buckets.items():
        percentage = (count / len(score_values)) * 100
        print(f"  {risk_level}: {count} wallets ({percentage:.1f}%)")

def plot_risk_distribution(scores):
    import matplotlib.pyplot as plt
    score_values = list(scores.values())
    bins = [0, 200, 400, 600, 800, 1000]
    labels = ['Low (0-200)', 'Medium-Low (201-400)', 'Medium (401-600)', 'High (601-800)', 'Very High (801-1000)']
    plt.hist(score_values, bins=bins, edgecolor='black')
    plt.xlabel('Risk Score')
    plt.ylabel('Number of Wallets')
    plt.title('Risk Score Distribution')
    plt.xticks(bins, labels, rotation=45)
    plt.tight_layout()
    plt.savefig('output/risk_distribution.png')
    plt.close()        

def main():
    """Main execution function."""
    print("="*60)
    print("DeFi WALLET RISK SCORING SYSTEM")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup
    setup_directories()
    
    # Load wallet addresses
    print("\n📁 Loading wallet addresses...")
    wallet_addresses = load_wallet_addresses()
    
    # Initialize components
    print("\n🔧 Initializing system components...")
    data_collector = CompoundDataCollector()
    feature_extractor = RiskFeatureExtractor()
    risk_scorer = WalletRiskScorer()
    
    # Process wallets
    print(f"\n🔍 Processing {len(wallet_addresses)} wallets...")
    scores = {}
    detailed_analysis = {}
    errors = []
    
    for i, wallet in enumerate(wallet_addresses, 1):
        try:
            print(f"Processing wallet {i}/{len(wallet_addresses)}: {wallet[:10]}...")
            
            # Collect transaction data
            tx_data = data_collector.get_wallet_transactions(wallet)
            
            # Extract features
            features = feature_extractor.extract_features(wallet, tx_data)
            
            # Calculate risk score
            risk_score = risk_scorer.calculate_risk_score(features)
            
            # Store results
            scores[wallet] = risk_score
            detailed_analysis[wallet] = {
                'total_score': risk_score,
                'features': features,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            print(f"  ✓ Risk Score: {risk_score}")
            
            # Rate limiting
            time.sleep(0.2)  # 5 requests per second
            
        except Exception as e:
            error_msg = f"Error processing {wallet}: {str(e)}"
            print(f"  ❌ {error_msg}")
            errors.append(error_msg)
            
            # Assign default score for failed wallets
            scores[wallet] = DEFAULT_RISK_SCORE
            detailed_analysis[wallet] = {
                'total_score': DEFAULT_RISK_SCORE,
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    # Save results
    print(f"\n💾 Saving results...")
    output_file, detailed_file = save_results(scores, detailed_analysis)
    
    # Print summary
    print_summary_statistics(scores)
    
    # Plot risk distribution
    plot_risk_distribution(scores)
    
    # Print errors if any
    if errors:
        print(f"\n⚠️  Errors encountered:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 Results saved to: {output_file}")
    print(f"📋 Detailed analysis: {detailed_file}")
    print(f"⏱️  Total execution time: {time.time() - start_time:.1f} seconds")

if __name__ == "__main__":
    start_time = time.time()
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)