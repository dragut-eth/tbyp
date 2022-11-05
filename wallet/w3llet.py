from os import environ as config
from time import sleep
from web3 import Web3
from web3.middleware import geth_poa_middleware, construct_sign_and_send_raw_middleware

import main

INITIAL_AMOUNT = 100
NEW_ACCOUNT_PRICE = 50
DECIMALS = 6

BLOCKCHAIN_RCP_URL = config['BLOCKCHAIN_RCP_URL']
CONTRACT_OWNER_KEY = config['CONTRACT_OWNER_KEY']
CONTRACT_ADDRESS = config['CONTRACT_ADDRESS']

w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_RCP_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
if not w3.isConnected():
    raise Exception("Web3 Connexion Error")

account = w3.eth.account.from_key(CONTRACT_OWNER_KEY)
w3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))
w3.eth.default_account  = account.address

with open("solidity/TBYPCoin.abi") as f:
     abi = f.read()
 
Contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

class Wallet:
    def __init__(self, address):
        self.address = address
        self.get_coin()

    def createAccount(self, name):
        if len(name)<3 or len(name)>32:
            return False
        handle = main._find_handle(name)
        if not handle:
            return False
        self.init_coin(INITIAL_AMOUNT)
        if not self.pay(NEW_ACCOUNT_PRICE):
            return False
        return main._create_account(self.address, handle, name)

    def get_coin(self):
        tx_hash = Contract.functions.totalBalanceOf(self.address).call()
        self.coin = tx_hash[0]/10**DECIMALS
        self.stake = tx_hash[1]/10**DECIMALS
        return True

    def init_coin(self, amount):
        if not hasattr(self, 'coin' ) or self.coin==0:
            status = _transact('addCredit', self.address, int(amount*10**DECIMALS))
            self.coin = amount
            return status
        return True

    def transfer(self, amount, target ):
        return _transact('transferFrom', self.address, target, int(amount*10**DECIMALS))

    def pay(self, amount ):
        return _transact('pay', self.address, int(amount*10**DECIMALS))

    def earn(self, amount ):
        return _transact('addCredit', self.address, int(amount*10**DECIMALS))

    def pay_stake(self, amount, stake):
        return _transact('payAndStake', self.address, int(amount*10**DECIMALS), int(stake*10**DECIMALS))

    def unlock(self, amount, reward=0):
        return _transact('unlockStake',self.address, int(amount*10**DECIMALS), int(reward*10**DECIMALS))

def _transact(function, address, *argv):
    for tries in range(5): 
        nonce =  w3.eth.get_transaction_count(account.address)
        try:
            tx_hash = getattr(Contract.functions,function)(address, *argv).transact({'nonce': nonce, 'gasPrice': 1000000000})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        except ValueError as e:
            if isinstance( e.args[0], dict):
                error = e.args[0].get('message', str(e))
                if error == "nonce too low":
                    continue
                elif error=="already known" or error=='replacement transaction underpriced':
                    sleep(5) # give time for pending transaction to execute
                    continue
            raise
        except BaseException:
            raise
        else:
            return (receipt['status']==1)
    
    raise RuntimeError("Chaine too busy, try again later")
 