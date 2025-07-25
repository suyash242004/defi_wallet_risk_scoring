"""
Data Collector for Compound Protocol Transactions
Fetches transaction data from Etherscan API and The Graph Protocol
"""

import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
# from config.config import *
from config.config import API_RATE_LIMIT, MAX_RETRIES, REQUEST_TIMEOUT, BATCH_SIZE
from config.api_keys import ETHERSCAN_API_KEY

class CompoundDataCollector:
    """Collects transaction data from various sources for Compound protocol analysis."""
    
    def __init__(self):
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        if not self.etherscan_api_key:
            raise ValueError("ETHERSCAN_API_KEY environment variable not set")
        
        self.etherscan_base_url = "https://api.etherscan.io/api"
        self.compound_subgraph_url = "https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v2"
        
        # Compound contract addresses
        self.compound_contracts = {
            'comptroller': '0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b',
            'ceth': '0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5',
            'cdai': '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643',
            'cusdc': '0x39aa39c021dfbae8fac545936693ac917d5e7563',
            'cwbtc': '0xc11b1268c1a384e55c48c2391d8d480264a3a7f4'
        }
        
        self.session = requests.Session()
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce rate limiting for API calls."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / API_RATE_LIMIT
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _make_etherscan_request(self, params: Dict) -> Dict:
        """Make a rate-limited request to Etherscan API."""
        self._rate_limit()
        
        params['apikey'] = self.etherscan_api_key
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(self.etherscan_base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == '1':
                    return data
                elif data.get('message') == 'No transactions found':
                    return {'result': []}
                else:
                    print(f"Etherscan API error: {data.get('message')}")
                    
            except requests.exceptions.RequestException as e:
                print(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                
        return {'result': []}
    
    def get_wallet_transactions(self, wallet_address: str) -> Dict:
        """Get comprehensive transaction data for a wallet."""
        print(f"  📡 Fetching data for {wallet_address[:10]}...")
        
        # Get regular transactions
        normal_txs = self._get_normal_transactions(wallet_address)
        
        # Get internal transactions
        internal_txs = self._get_internal_transactions(wallet_address)
        
        # Get ERC-20 token transactions
        token_txs = self._get_token_transactions(wallet_address)
        
        # Get current balances
        current_balances = self._get_current_balances(wallet_address)
        
        # Filter for Compound-related transactions
        compound_txs = self._filter_compound_transactions(normal_txs, token_txs)
        
        # Get Compound-specific data from subgraph
        compound_data = self._get_compound_subgraph_data(wallet_address)
        
        return {
            'wallet_address': wallet_address,
            'normal_transactions': normal_txs,
            'internal_transactions': internal_txs,
            'token_transactions': token_txs,
            'compound_transactions': compound_txs,
            'current_balances': current_balances,
            'compound_data': compound_data,
            'data_timestamp': datetime.now().isoformat()
        }
    
    def _get_normal_transactions(self, wallet_address: str) -> List[Dict]:
        """Get normal Ethereum transactions."""
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': wallet_address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'desc'
        }
        
        data = self._make_etherscan_request(params)
        return data.get('result', [])
    
    def _get_internal_transactions(self, wallet_address: str) -> List[Dict]:
        """Get internal transactions."""
        params = {
            'module': 'account',
            'action': 'txlistinternal',
            'address': wallet_address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'desc'
        }
        
        data = self._make_etherscan_request(params)
        return data.get('result', [])
    
    def _get_token_transactions(self, wallet_address: str) -> List[Dict]:
        """Get ERC-20 token transactions."""
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': wallet_address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'desc'
        }
        
        data = self._make_etherscan_request(params)
        return data.get('result', [])
    
    def _get_current_balances(self, wallet_address: str) -> Dict:
        """Get current ETH and token balances."""
        balances = {}
        
        # Get ETH balance
        params = {
            'module': 'account',
            'action': 'balance',
            'address': wallet_address,
            'tag': 'latest'
        }
        
        data = self._make_etherscan_request(params)
        if data.get('result'):
            balances['ETH'] = int(data['result']) / 10**18
        
        return balances
    
    def _filter_compound_transactions(self, normal_txs: List[Dict], token_txs: List[Dict]) -> List[Dict]:
        """Filter transactions related to Compound protocol."""
        compound_txs = []
        
        # Filter normal transactions to Compound contracts
        for tx in normal_txs:
            if tx.get('to', '').lower() in [addr.lower() for addr in self.compound_contracts.values()]:
                tx['protocol'] = 'compound'
                tx['contract_type'] = self._identify_compound_contract(tx.get('to', ''))
                compound_txs.append(tx)
        
        # Filter token transactions for cTokens
        for tx in token_txs:
            contract_addr = tx.get('contractAddress', '').lower()
            if contract_addr in [addr.lower() for addr in self.compound_contracts.values()]:
                tx['protocol'] = 'compound'
                tx['token_type'] = 'cToken'
                compound_txs.append(tx)
        
        return compound_txs
    
    def _identify_compound_contract(self, contract_address: str) -> str:
        """Identify the type of Compound contract."""
        addr_lower = contract_address.lower()
        for name, address in self.compound_contracts.items():
            if addr_lower == address.lower():
                return name
        return 'unknown'
    
    def _get_compound_subgraph_data(self, wallet_address: str) -> Dict:
        """Get Compound-specific data from The Graph subgraph."""
        query = """
        {
          account(id: "%s") {
            id
            hasBorrowed
            countLiquidated
            countLiquidator
            tokens {
              id
              symbol
              cTokenBalance
              totalUnderlyingSupplied
              totalUnderlyingBorrowed
              totalUnderlyingRedeemed
              totalUnderlyingRepaid
              accountBorrowIndex
              totalUnderlyingBorrowedInUsd: totalUnderlyingBorrowed
              totalUnderlyingSuppliedInUsd: totalUnderlyingSupplied
            }
          }
        }
        """ % wallet_address.lower()
        
        try:
            response = requests.post(
                self.compound_subgraph_url,
                json={'query': query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
            else:
                print(f"Subgraph query failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Subgraph request error: {e}")
        
        return {}
    
    def get_compound_market_data(self) -> Dict:
        """Get current Compound market data."""
        query = """
        {
          markets {
            id
            symbol
            name
            underlyingAddress
            underlyingName
            underlyingSymbol
            borrowRate
            supplyRate
            exchangeRate
            collateralFactor
            totalSupply
            totalBorrows
            cash
            reserves
          }
        }
        """
        
        try:
            response = requests.post(
                self.compound_subgraph_url,
                json={'query': query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
                
        except requests.exceptions.RequestException as e:
            print(f"Market data request error: {e}")
        
        return {}
    
    def calculate_health_factor(self, wallet_data: Dict) -> float:
        """Calculate approximate health factor for a wallet."""
        compound_data = wallet_data.get('compound_data', {})
        account_data = compound_data.get('account')
        
        if not account_data or not account_data.get('tokens'):
            return 5.0  # Default high health factor for accounts with no data
        
        total_collateral_usd = 0
        total_borrow_usd = 0
        
        for token in account_data['tokens']:
            # Simplified calculation - in production, would need current prices
            supplied = float(token.get('totalUnderlyingSuppliedInUsd', 0))
            borrowed = float(token.get('totalUnderlyingBorrowedInUsd', 0))
            
            # Assume 75% collateral factor for simplification
            total_collateral_usd += supplied * 0.75
            total_borrow_usd += borrowed
        
        if total_borrow_usd == 0:
            return 5.0  # No debt = very healthy
        
        health_factor = total_collateral_usd / total_borrow_usd
        return min(health_factor, 10.0)  # Cap at 10 for display purposes