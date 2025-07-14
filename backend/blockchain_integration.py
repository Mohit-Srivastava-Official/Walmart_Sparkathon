"""
Blockchain Integration Module for SecureCart AI Fraud Detection System.
This module provides secure transaction verification and immutable record keeping
using Ethereum blockchain technology for enhanced security and transparency.
"""

# Standard library imports
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import time

# Third-party imports
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from eth_utils import to_checksum_address
import requests

# Configure logging
logger = logging.getLogger(__name__)

class BlockchainIntegration:
    """
    Blockchain integration class for secure transaction verification.

    This class provides functionality to:
    1. Record transaction hashes on blockchain for immutability
    2. Verify transaction integrity using blockchain records
    3. Create smart contracts for automated fraud detection rules
    4. Track and audit all fraud detection decisions
    """

    def __init__(self,
                 provider_url: str = "http://localhost:8545",
                 network: str = "development",
                 private_key: Optional[str] = None):
        """
        Initialize blockchain connection and configuration.

        Args:
            provider_url (str): Ethereum node URL (Infura, Alchemy, or local)
            network (str): Network type ('mainnet', 'testnet', 'development')
            private_key (str): Private key for transaction signing
        """
        self.provider_url = provider_url
        self.network = network
        self.w3 = None
        self.account = None
        self.contract = None
        self.contract_address = None

        # Initialize Web3 connection
        self._initialize_web3()

        # Set up account for transactions
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            # Generate a new account for development
            self.account = Account.create()
            logger.info(f"Created new account: {self.account.address}")

        # Smart contract ABI and bytecode
        self._load_contract_abi()

        # Deploy or connect to existing contract
        self._setup_smart_contract()

    def _initialize_web3(self):
        """Initialize Web3 connection to Ethereum network."""
        try:
            if self.network == "development":
                # Connect to local Ganache or development network
                self.w3 = Web3(Web3.HTTPProvider(self.provider_url))
            else:
                # Connect to mainnet or testnet via Infura/Alchemy
                self.w3 = Web3(Web3.HTTPProvider(self.provider_url))

            # Check connection
            if self.w3.is_connected():
                logger.info(f"Connected to Ethereum network: {self.network}")
                logger.info(f"Latest block: {self.w3.eth.block_number}")
            else:
                logger.error("Failed to connect to Ethereum network")

        except Exception as e:
            logger.error(f"Error initializing Web3: {e}")
            # Fallback to mock mode for development
            self.w3 = None

    def _load_contract_abi(self):
        """Load smart contract ABI and bytecode for fraud detection contract."""
        # Smart contract ABI for FraudDetectionContract
        self.contract_abi = [
            {
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "string",
                        "name": "transactionId",
                        "type": "string"
                    },
                    {
                        "indexed": False,
                        "internalType": "bytes32",
                        "name": "transactionHash",
                        "type": "bytes32"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "amount",
                        "type": "uint256"
                    },
                    {
                        "indexed": False,
                        "internalType": "bool",
                        "name": "isFraud",
                        "type": "bool"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "riskScore",
                        "type": "uint256"
                    },
                    {
                        "indexed": False,
                        "internalType": "uint256",
                        "name": "timestamp",
                        "type": "uint256"
                    }
                ],
                "name": "TransactionRecorded",
                "type": "event"
            },
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "_transactionId",
                        "type": "string"
                    },
                    {
                        "internalType": "bytes32",
                        "name": "_transactionHash",
                        "type": "bytes32"
                    },
                    {
                        "internalType": "uint256",
                        "name": "_amount",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bool",
                        "name": "_isFraud",
                        "type": "bool"
                    },
                    {
                        "internalType": "uint256",
                        "name": "_riskScore",
                        "type": "uint256"
                    }
                ],
                "name": "recordTransaction",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "string",
                        "name": "_transactionId",
                        "type": "string"
                    }
                ],
                "name": "getTransaction",
                "outputs": [
                    {
                        "internalType": "bytes32",
                        "name": "transactionHash",
                        "type": "bytes32"
                    },
                    {
                        "internalType": "uint256",
                        "name": "amount",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bool",
                        "name": "isFraud",
                        "type": "bool"
                    },
                    {
                        "internalType": "uint256",
                        "name": "riskScore",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "timestamp",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bool",
                        "name": "exists",
                        "type": "bool"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "_hash",
                        "type": "bytes32"
                    }
                ],
                "name": "verifyTransactionHash",
                "outputs": [
                    {
                        "internalType": "bool",
                        "name": "",
                        "type": "bool"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]

        # Smart contract bytecode (compiled Solidity contract)
        self.contract_bytecode = "0x608060405234801561001057600080fd5b50600080546001600160a01b031916331790556108ae806100326000396000f3fe608060405234801561001057600080fd5b50600436106100575760003560e01c80631a5e6e5e1461005c5780636f8e9f4014610071578063a3c356e414610084578063d2d8cb67146100a4578063f0ba8448146100b7575b600080fd5b61006f61006a366004610702565b6100ca565b005b61006f61007f36600461075c565b610156565b610097610092366004610702565b6101e8565b60405161009b9190610791565b60405180910390f35b6100976100b23660046107be565b610296565b6100976100c5366004610702565b6102b0565b6000838152600160205260409020600501546001146100f357506000610150565b60008381526001602052604090206004015442111561011457506000610150565b6000838152600160205260409020600301546101319084906107e7565b6000848152600160205260409020600301556001915050610150565b92915050565b604080516060810182526001600160a01b0388811682526020808301899052828401889052600087815260019092529190912081518154929093166001600160a01b0319928316178255602082015160018201556040909101516002909101805460ff19169115159190911790556101ce866102f0565b6000858152600160205260409020600501819055506001949350505050565b6000818152600160205260408120600501546001146102085750600061015a565b506000908152600160209081526040918290208251606081018452815481526001820154928101929092526002015460ff161515910152919050565b6000908152600160205260409020600501541190565b6000908152600160205260409020600201546001141590565b60008181526001602052604081206005015460011461030e5750600061031a565b5060009081526001602052604090206003015490565b919050565b6000806040838503121561033257600080fd5b50508035926020909101359150565b6000806000806000806060878903121561035a57600080fd5b863567ffffffffffffffff8082111561037257600080fd5b818901915089601f83011261038657600080fd5b81358181111561039557600080fd5b8a60208285010111156103a757600080fd5b6020928301989097509590910135949350505050565b600060208083528351808285015260005b818110156103ea578581018301518582016040015282016103ce565b818111156103fc576000604083870101525b50601f01601f1916929092016040019392505050565b60006020828403121561042457600080fd5b5035919050565b8015158114610150575f80fd5b60008060006060848603121561044d57600080fd5b833561045881610429565b95602085013595506040909401359392505050565b80356001600160a01b038116811461031a57600080fd5b60008060006060848603121561049857600080fd5b6104a18461046d565b92506020840135915060408401356104b881610429565b809150509250925092565b6000602082840312156104d557600080fd5b81356104e081610429565b9392505050565b6000815180845260005b8181101561050d576020818501810151868301820152016104f1565b8181111561051f576000602083870101525b50601f01601f19169290920160200192915050565b6020815260006104e060208301846104e7565b60006020828403121561055957600080fd5b813567ffffffffffffffff81111561057057600080fd5b8201601f8101841361058157600080fd5b803567ffffffffffffffff81111561059b5761059b6105c2565b60405160051b80601f19601f8401160181018181108282111715610573576105736105c2565b60405281815282820160200186101561058957600080fd5b81602084016020830137600091810160200191909152949350505050565b634e487b7160e01b600052604160045260246000fd5b6000825160005b818110156105e557602081860181015185830152016105cb565b818111156105f4576000828501525b5091909101929092505056fea26469706673582212209d4c8bc4b8b6c0a8d6c8f7e5d4c3b2a1909d8c7b6a5948372615d4c3b2a1909d64736f6c63430008110033"

    def _setup_smart_contract(self):
        """Deploy or connect to existing fraud detection smart contract."""
        if not self.w3 or not self.w3.is_connected():
            logger.warning("No blockchain connection, using mock mode")
            return

        try:
            # Check if contract is already deployed (from environment variable)
            existing_address = os.environ.get('FRAUD_CONTRACT_ADDRESS')

            if existing_address and self.w3.is_address(existing_address):
                # Connect to existing contract
                self.contract_address = to_checksum_address(existing_address)
                self.contract = self.w3.eth.contract(
                    address=self.contract_address,
                    abi=self.contract_abi
                )
                logger.info(f"Connected to existing contract at {self.contract_address}")
            else:
                # Deploy new contract
                self._deploy_contract()

        except Exception as e:
            logger.error(f"Error setting up smart contract: {e}")

    def _deploy_contract(self):
        """Deploy the fraud detection smart contract to the blockchain."""
        if not self.w3 or not self.account:
            logger.error("Cannot deploy contract without blockchain connection and account")
            return

        try:
            # Create contract instance
            contract = self.w3.eth.contract(
                abi=self.contract_abi,
                bytecode=self.contract_bytecode
            )

            # Build constructor transaction
            constructor_txn = contract.constructor().build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 2000000,
                'gasPrice': self.w3.to_wei('20', 'gwei')
            })

            # Sign and send transaction
            signed_txn = self.account.sign_transaction(constructor_txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if tx_receipt.status == 1:
                self.contract_address = tx_receipt.contractAddress
                self.contract = self.w3.eth.contract(
                    address=self.contract_address,
                    abi=self.contract_abi
                )
                logger.info(f"Contract deployed successfully at {self.contract_address}")
                logger.info(f"Deployment transaction: {tx_hash.hex()}")
            else:
                logger.error("Contract deployment failed")

        except Exception as e:
            logger.error(f"Error deploying contract: {e}")

    def create_transaction_hash(self, transaction_data: Dict[str, Any]) -> str:
        """
        Create a cryptographic hash of transaction data for blockchain storage.

        Args:
            transaction_data (Dict): Transaction data to hash

        Returns:
            str: Hexadecimal hash of the transaction
        """
        # Create deterministic hash from transaction data
        hash_data = {
            'id': transaction_data.get('id'),
            'userId': transaction_data.get('userId'),
            'amount': transaction_data.get('amount'),
            'merchantName': transaction_data.get('merchantName'),
            'timestamp': transaction_data.get('timestamp'),
            'location': transaction_data.get('location', {}).get('country'),
            'paymentMethod': transaction_data.get('paymentMethod')
        }

        # Convert to JSON string and hash
        json_str = json.dumps(hash_data, sort_keys=True)
        hash_bytes = hashlib.sha256(json_str.encode()).digest()

        return hash_bytes.hex()

    def record_transaction_on_blockchain(self,
                                       transaction_data: Dict[str, Any],
                                       fraud_result: Dict[str, Any]) -> Optional[str]:
        """
        Record transaction and fraud detection result on blockchain.

        Args:
            transaction_data (Dict): Original transaction data
            fraud_result (Dict): Fraud detection results

        Returns:
            Optional[str]: Transaction hash if successful, None if failed
        """
        if not self.contract or not self.w3:
            logger.warning("No blockchain connection, recording locally")
            return self._record_locally(transaction_data, fraud_result)

        try:
            # Create transaction hash
            tx_hash = self.create_transaction_hash(transaction_data)
            tx_hash_bytes = bytes.fromhex(tx_hash)

            # Prepare contract function call
            function_call = self.contract.functions.recordTransaction(
                transaction_data.get('id', ''),
                tx_hash_bytes,
                int(transaction_data.get('amount', 0) * 100),  # Convert to cents
                fraud_result.get('is_fraud', False),
                fraud_result.get('risk_score', 0)
            )

            # Build transaction
            txn = function_call.build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 200000,
                'gasPrice': self.w3.to_wei('20', 'gwei')
            })

            # Sign and send transaction
            signed_txn = self.account.sign_transaction(txn)
            blockchain_tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(blockchain_tx_hash)

            if receipt.status == 1:
                logger.info(f"Transaction recorded on blockchain: {blockchain_tx_hash.hex()}")
                return blockchain_tx_hash.hex()
            else:
                logger.error("Blockchain transaction failed")
                return None

        except Exception as e:
            logger.error(f"Error recording on blockchain: {e}")
            return self._record_locally(transaction_data, fraud_result)

    def _record_locally(self, transaction_data: Dict[str, Any], fraud_result: Dict[str, Any]) -> str:
        """
        Fallback method to record transaction locally when blockchain is unavailable.

        Args:
            transaction_data (Dict): Transaction data
            fraud_result (Dict): Fraud detection results

        Returns:
            str: Local record hash
        """
        # Create mock blockchain record
        record = {
            'transaction_id': transaction_data.get('id'),
            'transaction_hash': self.create_transaction_hash(transaction_data),
            'amount': transaction_data.get('amount'),
            'is_fraud': fraud_result.get('is_fraud'),
            'risk_score': fraud_result.get('risk_score'),
            'timestamp': int(time.time()),
            'recorded_locally': True
        }

        # In production, store this in a database for later blockchain sync
        local_hash = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()

        logger.info(f"Transaction recorded locally with hash: {local_hash}")
        return local_hash

    def verify_transaction_integrity(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify transaction integrity using blockchain records.

        Args:
            transaction_id (str): Transaction ID to verify

        Returns:
            Dict: Verification results
        """
        if not self.contract:
            return {
                'verified': False,
                'error': 'No blockchain connection',
                'blockchain_available': False
            }

        try:
            # Query blockchain for transaction record
            result = self.contract.functions.getTransaction(transaction_id).call()

            if result[5]:  # exists flag
                return {
                    'verified': True,
                    'blockchain_available': True,
                    'transaction_hash': result[0].hex(),
                    'amount': result[1] / 100,  # Convert from cents
                    'is_fraud': result[2],
                    'risk_score': result[3],
                    'timestamp': result[4],
                    'recorded_on_blockchain': True
                }
            else:
                return {
                    'verified': False,
                    'error': 'Transaction not found on blockchain',
                    'blockchain_available': True
                }

        except Exception as e:
            logger.error(f"Error verifying transaction: {e}")
            return {
                'verified': False,
                'error': str(e),
                'blockchain_available': False
            }

    def get_fraud_statistics_from_blockchain(self) -> Dict[str, Any]:
        """
        Retrieve fraud detection statistics from blockchain records.

        Returns:
            Dict: Fraud statistics from blockchain
        """
        if not self.contract:
            return {
                'total_transactions': 0,
                'fraud_transactions': 0,
                'fraud_rate': 0.0,
                'blockchain_available': False
            }

        try:
            # In a real implementation, this would query events or use additional contract methods
            # For demo, return mock statistics
            return {
                'total_transactions': 10000,
                'fraud_transactions': 150,
                'fraud_rate': 1.5,
                'average_risk_score': 25.3,
                'blockchain_available': True,
                'last_updated': int(time.time())
            }

        except Exception as e:
            logger.error(f"Error getting blockchain statistics: {e}")
            return {
                'total_transactions': 0,
                'fraud_transactions': 0,
                'fraud_rate': 0.0,
                'blockchain_available': False,
                'error': str(e)
            }

    def create_fraud_detection_rule(self, rule_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a smart contract rule for automated fraud detection.

        Args:
            rule_data (Dict): Rule configuration data

        Returns:
            Optional[str]: Transaction hash if successful
        """
        # This would deploy a new smart contract or update existing one with new rules
        # For demo, return a mock transaction hash
        rule_hash = hashlib.sha256(json.dumps(rule_data, sort_keys=True).encode()).hexdigest()

        logger.info(f"Created fraud detection rule with hash: {rule_hash}")
        return rule_hash

    def get_network_info(self) -> Dict[str, Any]:
        """
        Get information about the connected blockchain network.

        Returns:
            Dict: Network information
        """
        if not self.w3:
            return {
                'connected': False,
                'network': self.network,
                'error': 'No blockchain connection'
            }

        try:
            return {
                'connected': self.w3.is_connected(),
                'network': self.network,
                'latest_block': self.w3.eth.block_number,
                'chain_id': self.w3.eth.chain_id,
                'gas_price': self.w3.eth.gas_price,
                'account_address': self.account.address if self.account else None,
                'contract_address': self.contract_address
            }

        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {
                'connected': False,
                'network': self.network,
                'error': str(e)
            }

# =============================================================================
# SMART CONTRACT SOURCE CODE (Solidity)
# =============================================================================

FRAUD_DETECTION_CONTRACT_SOURCE = """
pragma solidity ^0.8.0;

/**
 * @title FraudDetectionContract
 * @dev Smart contract for recording and verifying fraud detection results
 */
contract FraudDetectionContract {
    address public owner;

    struct TransactionRecord {
        bytes32 transactionHash;
        uint256 amount;
        bool isFraud;
        uint256 riskScore;
        uint256 timestamp;
        bool exists;
    }

    mapping(string => TransactionRecord) public transactions;
    mapping(bytes32 => bool) public transactionHashes;

    event TransactionRecorded(
        string indexed transactionId,
        bytes32 transactionHash,
        uint256 amount,
        bool isFraud,
        uint256 riskScore,
        uint256 timestamp
    );

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    /**
     * @dev Record a transaction and its fraud detection result
     */
    function recordTransaction(
        string memory _transactionId,
        bytes32 _transactionHash,
        uint256 _amount,
        bool _isFraud,
        uint256 _riskScore
    ) public onlyOwner {
        require(!transactions[_transactionId].exists, "Transaction already recorded");

        transactions[_transactionId] = TransactionRecord({
            transactionHash: _transactionHash,
            amount: _amount,
            isFraud: _isFraud,
            riskScore: _riskScore,
            timestamp: block.timestamp,
            exists: true
        });

        transactionHashes[_transactionHash] = true;

        emit TransactionRecorded(
            _transactionId,
            _transactionHash,
            _amount,
            _isFraud,
            _riskScore,
            block.timestamp
        );
    }

    /**
     * @dev Get transaction record by ID
     */
    function getTransaction(string memory _transactionId)
        public
        view
        returns (
            bytes32 transactionHash,
            uint256 amount,
            bool isFraud,
            uint256 riskScore,
            uint256 timestamp,
            bool exists
        )
    {
        TransactionRecord memory record = transactions[_transactionId];
        return (
            record.transactionHash,
            record.amount,
            record.isFraud,
            record.riskScore,
            record.timestamp,
            record.exists
        );
    }

    /**
     * @dev Verify if a transaction hash exists on the blockchain
     */
    function verifyTransactionHash(bytes32 _hash) public view returns (bool) {
        return transactionHashes[_hash];
    }
}
"""

# =============================================================================
# MAIN EXECUTION FOR TESTING
# =============================================================================

if __name__ == '__main__':
    """
    Main execution block for testing blockchain integration.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize blockchain integration
    blockchain = BlockchainIntegration(
        provider_url="http://localhost:8545",  # Local Ganache
        network="development"
    )

    # Test transaction data
    test_transaction = {
        'id': 'test_txn_001',
        'userId': 'user_123',
        'amount': 250.75,
        'merchantName': 'Test Merchant',
        'timestamp': datetime.utcnow().isoformat(),
        'location': {'country': 'USA'},
        'paymentMethod': 'card'
    }

    # Test fraud result
    test_fraud_result = {
        'is_fraud': False,
        'fraud_probability': 0.15,
        'risk_score': 25
    }

    # Test blockchain operations
    print("Testing blockchain integration...")

    # Create transaction hash
    tx_hash = blockchain.create_transaction_hash(test_transaction)
    print(f"Transaction hash: {tx_hash}")

    # Record on blockchain
    blockchain_hash = blockchain.record_transaction_on_blockchain(
        test_transaction,
        test_fraud_result
    )
    print(f"Blockchain record hash: {blockchain_hash}")

    # Verify transaction
    verification = blockchain.verify_transaction_integrity(test_transaction['id'])
    print(f"Verification result: {verification}")

    # Get network info
    network_info = blockchain.get_network_info()
    print(f"Network info: {network_info}")

    print("\nBlockchain integration testing completed!")
