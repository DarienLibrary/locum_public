from . import queries


def get_balance(patron_barcode):
    edb = queries.Database()
    balance = edb.get_balance(patron_barcode)
    if balance:
        balance_str = '{:0.2f}'.format(int(balance) / 100.0)
        return {
            'balance': balance_str,
            'success': True
        }
    return {"success": False}