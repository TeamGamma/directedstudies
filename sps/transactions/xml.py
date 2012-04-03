from lxml import etree
from lxml import objectify
import logging
from datetime import datetime

ElementMaker = objectify.ElementMaker(annotate=False)
Quote = ElementMaker.quote
Error = ElementMaker.error
Result = ElementMaker.result
Response = ElementMaker.response
Transactions = ElementMaker.transactions
Transaction = ElementMaker.transaction
Triggers = ElementMaker.triggers
Trigger = ElementMaker.trigger
Stocks = ElementMaker.stocks
Stock = ElementMaker.stock
AccountBalance = ElementMaker.account_balance
ReserveBalance = ElementMaker.reserve_balance
Log = ElementMaker.log
Event = ElementMaker.event

#configure logging format for transaction logs
TransactionLog = logging.getLogger("TransactionLogs")

class QuoteResponse():
    def __init__(self, quantity, price):
        self.quantity = quantity
        self.price = price

    def __str__(self):
        xml = Response(
            Quote(str(self.price), quantity=str(self.quantity)),
            contents='quote')
        return etree.tostring(xml)

class ErrorResponse():
    def __init__(self, exception):
        self.exception = exception

    def __str__(self):
        xml = Response(Error(self.exception.message), contents='error')
        return etree.tostring(xml)

class ResultResponse():
    def __init__(self, message):
        self.message = message

    def __str__(self):
        xml = Response(Result(self.message), contents='result')
        return etree.tostring(xml)


class DumplogResponse():
    def __init__(self, transactions):
        self.transactions = transactions

    def __str__(self):
        xml = Response(Transactions(
            *[transaction_element(t) for t in self.transactions]
        ), contents='dumplog')
        return etree.tostring(xml)


class SummaryResponse():
    def __init__(self, transactions, triggers, stocks,
            account_balance, reserve_balance):
        self.transactions = transactions
        self.triggers = triggers
        self.stocks = stocks
        self.account_balance = account_balance
        self.reserve_balance = reserve_balance

    def __str__(self):
        xml = Response(
            AccountBalance(str(self.account_balance)),
            ReserveBalance(str(self.reserve_balance)),
            Transactions(
                *[transaction_element(t) for t in self.transactions]
            ),
            Stocks(
                *[stock_element(s) for s in self.stocks]
            ),
            Triggers(
                *[trigger_element(t) for t in self.triggers]
            ),
            contents='summary'
        )
        return etree.tostring(xml)


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
        creation_time=str(t.creation_time))

def trigger_element(t):
    """ Converts a Trigger to an XML element class """
    return Trigger(
        id=str(t.id),
        username=t.username,
        stock_symbol=t.stock_symbol,
        trigger_value=str(t.trigger_value),
        amount=str(t.amount),
        quantity=str(t.quantity),
        state=str(t.state),
        operation=t.operation)

def stock_element(s):
    """ Converts a StockPurchase to an XML element class """
    return Stock(
        username=s.username,
        stock_symbol=s.stock_symbol,
        quantity=str(s.quantity))


def log_transaction(transaction_type, db_transaction, status_message=None):
    if status_message == None:
        xml = Log(transaction_element(db_transaction), type=transaction_type, time=str(datetime.now()))
    else:
        xml = Log(transaction_element(db_transaction), type=transaction_type, status_message=status_message, time=str(datetime.now()))

    # write a transaction log message to STDOUT that has the string of the XML tags 
    TransactionLog.info(etree.tostring(xml))

def log_trigger(trigger_type, db_trigger, status_message=None):

    if status_message == None:
        xml = Log(trigger_element(db_trigger), type=trigger_type, time=str(datetime.now()))
    else:
        xml = Log(trigger_element(db_trigger), type=trigger_type, status_message=status_message, time=str(datetime.now()))

    # write a transaction log message to STDOUT that has the string of the XML tags 
    TransactionLog.info(etree.tostring(xml))

def log_event(event_type, username, stock_symbol=None, amount=None, status_message=None):

    xml = Log(
        Event(type=event_type, username=username, 
            stock_symbol=str(stock_symbol), amount=str(amount), 
            status_message=str(status_message), time=str(datetime.now()))
    )

    # write a transaction log message to STDOUT that has the string of the XML tags 
    TransactionLog.info(etree.tostring(xml))

def log_error(command, message):

    xml = Log(Event(command=command, error_message=message, time=str(datetime.now())))

    # write a transaction log message to STDOUT that has the string of the XML tags 
    TransactionLog.error(etree.tostring(xml))

