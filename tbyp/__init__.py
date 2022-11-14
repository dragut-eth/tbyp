from os import environ as config

from . import main
from .database import initialize as tytb_initialize

if config['WEB3'] == 'True':
    from .w3llet import Wallet
    from .user import User
else:
    from .wallet import Wallet
    from .user import User
