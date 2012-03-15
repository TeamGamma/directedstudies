COMMANDS = (
    'ADD',
    'QUOTE',

    'BUY',
    'COMMIT_BUY',
    'CANCEL_BUY',

    'SELL',
    'COMMIT_SELL',
    'CANCEL_SELL',

    'SET_BUY_AMOUNT',
    'SET_BUY_TRIGGER',
    'CANCEL_SET_BUY',

    'SET_SELL_AMOUNT',
    'SET_SELL_TRIGGER',
    'CANCEL_SET_SELL',

    'DUMPLOG_USER',
    'DUMPLOG',

    'DISPLAY_SUMMARY',
)

_username_input = dict(name='username', label='User ID', help='Your account login')
_stock_symbol_input = dict(name='stock_symbol', label='Stock Symbol', help='The stock symbol')
_money_value_input = dict(name='money value', label='Amount', help='Amount in dollars')
_quantity_input = dict(name='stock quantity', label='Quantity', help='Quantity of stock')
_buy_trigger_input = dict(name='money value', label='Trigger Price', help='Buy will be triggered stock price goes below this')
_sell_trigger_input = dict(name='money value', label='Trigger Price', help='Sell will be triggered stock price goes above this')
_filename_input = dict(name='filename', label='Output File', help='Write to this file')

class ADD():
    description = "Add money to your account"
    inputs = (
        _username_input,
        _money_value_input,
    )

class QUOTE():
    description = "Get a quote for a stock symbol"
    inputs = (
        _username_input,
        _stock_symbol_input,
    )

class BUY():
    description = "Buy some stock."
    inputs = (
        _username_input,
        _stock_symbol_input,
        _money_value_input,
    )

class COMMIT_BUY():
    description = "Commit your last buy transaction"
    inputs = (
        _username_input,
    )

class CANCEL_BUY():
    description = "Cancel your last buy transaction"
    inputs = (
        _username_input,
    )

class SELL():
    description = "Sell some of your stock"
    inputs = (
        _username_input,
        _stock_symbol_input,
        _quantity_input,
    )

class COMMIT_SELL():
    description = "Commit your last sell transaction"
    inputs = (
        _username_input,
    )

class CANCEL_SELL():
    description = "Cancel your last sell transaction"
    inputs = (
        _username_input,
    )

class SET_BUY_TRIGGER():
    description = "Set the trigger point for an automatic buy and start the trigger"
    inputs = (
        _username_input,
        _stock_symbol_input,
        _money_value_input,
    )

class SET_SELL_TRIGGER():
    description = "Set the trigger point for an automatic sell and start the trigger"
    inputs = (
        _username_input,
        _stock_symbol_input,
        _money_value_input,
    )

class SET_BUY_AMOUNT():
    description = "Create a trigger and reserve account to automatically buy stock"
    inputs = (
        _username_input,
        _stock_symbol_input,
        _money_value_input,
    )

class SET_SELL_AMOUNT():
    description = "Create a trigger to automatically sell stock"
    inputs = (
        _username_input,
        _stock_symbol_input,
        _quantity_input,
    )

class CANCEL_SET_BUY():
    description = "Cancel your last automatic buy trigger and remove its reserve account"
    inputs = (
        _username_input,
        _stock_symbol_input,
    )

class CANCEL_SET_SELL():
    description = "Cancel your last automatic sell trigger"
    inputs = (
        _username_input,
        _stock_symbol_input,
    )

class DUMPLOG_USER():
    description = "Dump your account transactions to a file"
    inputs = (
        _username_input,
        _filename_input,
    )

class DUMPLOG():
    description = "Dump all transactions to a file (ADMIN ONLY)"
    inputs = (
        _filename_input,
    )

class DISPLAY_SUMMARY():
    description = "Display summary of your accounts, triggers, and transactions"
    inputs = (
        _username_input,
    )


# Generate a "nice version" of each command name
for cls_name in COMMANDS:
    cls = locals()[cls_name]
    cls.label = ' '.join((word.capitalize() for word in cls.__name__.split('_')))

