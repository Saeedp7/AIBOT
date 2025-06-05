# test_connection.py

from connectors.mt5_connector import initialize_mt5, shutdown_mt5, get_account_info

def test_mt5_connection():
    try:
        initialize_mt5()
        account_info = get_account_info()
        print("💼 Account Info:")
        print(f"Login: {account_info.login}")
        print(f"Balance: {account_info.balance}")
        print(f"Leverage: {account_info.leverage}")
        print(f"Currency: {account_info.currency}")
    except Exception as e:
        print(e)
    finally:
        shutdown_mt5()

if __name__ == "__main__":
    test_mt5_connection()
