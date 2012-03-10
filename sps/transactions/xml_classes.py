from lxml import etree
from lxml import objectify

ElementMaker = objectify.ElementMaker(annotate=False)
Response = ElementMaker.response
Transactions = ElementMaker.transactions
Transaction = ElementMaker.transaction
Triggers = ElementMaker.triggers
Trigger = ElementMaker.trigger
AccountBalance = ElementMaker.account_balance
ReserveAccount = ElementMaker.reserve_account

class QuoteResponse():
    def __init__(self, value):
        self.value = value

    def __str__(self):
        Quote = ElementMaker.quote
        xml = Response(Quote(str(self.value)), contents='quote')
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
            *[transaction_element(t) for t in self.transactions]
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
        xml = Response(
            Transactions(
                *[transaction_element(t) for t in self.transactions]
            ),
            Triggers(
                *[trigger_element(t) for t in self.triggers]
            ),
            AccountBalance(str(self.account_balance)),
            ReserveAccount(str(self.reserve_balance))
        )
        return etree.tostring(xml, pretty_print=True)


def transaction_element(t):
    """ Converts a Transaction to an XML element class """
    return Transaction(
        id=str(t.id),
        username=t.username,
        stock_symbol=t.stock_symbol,
        operation=t.operation,
        quantity=str(t.quantity),
        stock_value=str(t.stock_value),
        committed=str(t.committed),
        creation_time=str(t.creation_time)
    )

def trigger_element(t):
    """ Converts a SetTransaction to an XML element class """
    return Trigger(
        id=str(t.id),
        username=t.username,
        stock_symbol=t.stock_symbol,
        trigger_value=str(t.trigger_value),
        amount=str(t.amount),
        quantity=str(t.quantity),
        active=str(t.active),
        operation=t.operation,
    )


