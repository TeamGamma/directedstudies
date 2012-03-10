from lxml import etree
from lxml import objectify

ElementMaker = objectify.ElementMaker(annotate=False)
Response = ElementMaker.response
Transactions = ElementMaker.transactions
Transaction = ElementMaker.transaction
Triggers = ElementMaker.triggers
Trigger = ElementMaker.trigger
AccountBalance = ElementMaker.accountbalance
ReserveAccount = ElementMaker.reserveraccount

class QuoteResponse():
    def __init__(self, value):
        self.value = value

    def __str__(self):
        Quote = ElementMaker.quote
        xml = Response(Quote(self.value), contents='quote')
        return etree.tostring(xml)

class Error():
    def __init__(self, exception):
        self.exception = exception

    def __str__(self):
        Error = ElementMaker.error
        xml = Response(Error(self.exception.message), contents='error')
        return etree.tostring(xml)

class Result():
    def __init__(self, message):
        self.message = message

    def __str__(self):
        Result = ElementMaker.result
        xml = Response(Result(self.message), contents='results')
        return etree.tostring(xml)


class Dumplog():
    def __init__(self, transactions):
        self.transactions = transactions

    def __str__(self):
        xml = Response(Transactions(
            *[
            Transaction(
                id=str(t.id),
                username=t.username,
                user=t.user,
                stock_symbol=t.stock_symbol,
                operation=t.operation,
                quantity=t.quantity,
                stock_value=t.stock_value,
                committed=t.committed,
                creation_time=t.creation_time
            )
            for t in self.transactions
            ]
        ))
        return etree.tostring(xml, pretty_print=True)

class Summary():
    def __init__(self, transactions, triggers,
            account_balance, reserve_balance):
        self.transactions = transactions
        self.triggers = triggers
        self.account_balance = account_balance
        self.reserve_balance = reserve_balance

    def __str__(self):
        xml = Response(Transactions(
            *[
            Transaction(
                id=str(t.id),
                username=t.username,
                user=t.user,
                stock_symbol=t.stock_symbol,
                operation=t.operation,
                quantity=t.quantity,
                stock_value=t.stock_value,
                committed=t.committed,
                creation_time=t.creation_time
            )
            for t in self.transactions
            ]
        ),
                    Triggers(
            *[
            Trigger(
                id=str(t.id),
                username=t.username,
                user=t.user,
                stock_symbol=t.stock_symbol,
                stock_value=t.stock_value,
                operation=t.operation,
                quantity=t.quantity,
                creation_time=t.creation_time
            )
            for t in self.triggers
            ]
        ),
                    AccountBalance(
            self.account_balance
        ),
                    ReserveAccount(
            self.reserve_account
        )
        )
        return etree.tostring(xml, pretty_print=True)





