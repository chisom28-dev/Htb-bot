
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# MT5 is available only on supported Windows environments.
mt5 = None

if sys.platform == "win32":
    try:
        import MetaTrader5 as mt5_module
        mt5 = mt5_module
    except ImportError:
        logger.warning("MetaTrader5 package is not installed.")


class MT5Connector:
    def __init__(self):
        self.connected = False

    def connect(
        self,
        login: int,
        password: str,
        server: str,
        terminal_path: Optional[str] = None,
    ):
        if mt5 is None:
            return {
                "success": False,
                "message": (
                    "MT5 integration requires Windows and "
                    "the MetaTrader5 Python package."
                ),
            }

        if self.connected:
            return {
                "success": True,
                "message": "MT5 is already connected.",
            }

        initialized = (
            mt5.initialize(path=terminal_path)
            if terminal_path
            else mt5.initialize()
        )

        if not initialized:
            error = mt5.last_error()
            return {
                "success": False,
                "message": f"MT5 initialization failed: {error}",
            }

        authorized = mt5.login(
            login=int(login),
            password=password,
            server=server,
        )

        if not authorized:
            error = mt5.last_error()
            mt5.shutdown()

            return {
                "success": False,
                "message": f"MT5 login failed: {error}",
            }

        self.connected = True

        return {
            "success": True,
            "message": "MT5 connected successfully.",
            "account": self.get_account_info(),
        }

    def get_account_info(self):
        if mt5 is None or not self.connected:
            return None

        account = mt5.account_info()

        if account is None:
            return None

        return {
            "login": account.login,
            "server": account.server,
            "currency": account.currency,
            "balance": account.balance,
            "equity": account.equity,
            "leverage": account.leverage,
            "trade_allowed": account.trade_allowed,
        }

    def get_status(self):
        if mt5 is None:
            return {
                "connected": False,
                "message": "MT5 is unavailable in this environment.",
            }

        terminal = mt5.terminal_info() if self.connected else None

        return {
            "connected": self.connected and terminal is not None,
            "message": (
                "MT5 connected."
                if self.connected and terminal is not None
                else "MT5 disconnected."
            ),
        }

    def disconnect(self):
        if mt5 is not None and self.connected:
            mt5.shutdown()

        self.connected = False

        return {
            "success": True,
            "message": "MT5 disconnected.",
        }


mt5_connector = MT5Connector()
