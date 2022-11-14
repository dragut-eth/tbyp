from .database import execute, fetchone, commit, rowcount
from . import main

INITIAL_VALUE = 100
NEW_ACCOUNT_PRICE = 50

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
        self.init_coin(INITIAL_VALUE)
        if not self.pay(NEW_ACCOUNT_PRICE):
            return False
        return main._create_account(self.address, handle, name)

    def list_profiles(self):
        return main._list_profiles(self.address)

    def get_coin(self):
        execute("SELECT value,stake FROM coin WHERE address=%s", (self.address,))
        row=fetchone()
        if not row:
            return False
        self.coin = round(row['value'],2)
        self.stake = round(row['stake'],2)
        return True

    def transfer(self, value, target ):
        execute("UPDATE coin SET value=value-%(value)s WHERE address=%(address)s AND value-%(value)s>=0", {"address": self.address, "value": value})
        commit()
        if rowcount() == 0:
            return False
        execute("UPDATE coin SET value=value+%(value)s WHERE address=%(address)s", {"address": target, "value": value})
        commit()
        return True

    def pay(self, value ):
        execute("UPDATE coin SET value=value-%(value)s WHERE address=%(address)s AND value-%(value)s>=0", {"address": self.address, "value": value})
        commit()
        if rowcount() == 0:
            return False
        return True

    def earn(self, value ):
        execute("UPDATE coin SET value=value+%(value)s WHERE address=%(address)s", {"address": self.address, "value": value})
        commit()
        return True

    def init_coin(self, initial_value):
        if not hasattr(self, 'coin'):
            execute("INSERT INTO coin(address,value) VALUES (%(address)s, %(value)s)", {"address": self.address, "value": initial_value})
            commit()
            self.coin = initial_value

    def pay_stake(self, value, stake):
        if not self.pay(value+stake):
            return False
        execute("UPDATE coin SET stake=stake+%(stake)s WHERE address=%(address)s", {"address": self.address, "stake": stake})
        commit()
        return True

    def unlock(self, stake, reward=0):
        execute("UPDATE coin SET stake=stake-%(stake)s WHERE address=%(address)s AND value-%(stake)s>=0", {"address": self.address, "stake": stake})
        commit()
        if rowcount() == 0:
            return False
        return self.earn(stake+reward)