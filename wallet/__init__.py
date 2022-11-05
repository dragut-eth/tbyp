from os import environ as config

if config['WEB3'] == 'True':
    from .w3llet import Wallet
else:
    from .wallet import Wallet
