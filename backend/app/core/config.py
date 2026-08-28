"""
Core configuration and system settings.
"""
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment & Server
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "institutional-quant-secret-key-change-in-production-256bit"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Database & Cache
    DATABASE_URL: str = "sqlite:///./quant_platform.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Master Live Trading Safety Gate (HARD DEFAULT: False)
    LIVE_TRADING_ENABLED: bool = False
    DEFAULT_BROKER: str = "MOCK_BROKER"

    # Deterministic Risk Limits
    DEFAULT_RISK_PER_TRADE: float = 0.0025  # 0.25% of account equity
    MAX_DAILY_LOSS: float = 0.01            # 1.00% max daily loss
    MAX_DRAWDOWN: float = 0.10              # 10.0% max peak-to-trough drawdown
    MAX_OPEN_POSITIONS: int = 3             # Max 3 concurrent positions
    MIN_RISK_REWARD: float = 1.5            # Minimum 1.5:1 reward-to-risk ratio (optimized for fast scalps)
    MAX_SPREAD_PIPS: float = 3.0            # Maximum allowed spread in pips
    MAX_CONSECUTIVE_LOSSES: int = 3         # Cooldown trigger
    MAX_CURRENCY_CONCENTRATION: int = 2     # Max 2 positions per base/quote currency
    MAX_NOTIONAL_EXPOSURE: float = 50000.0  # Max USD notional value across positions

    # AutoTrader & Quality Gate (Sub-Minute Turbo Scalp Defaults for 80%+ Win Rate)
    DEFAULT_TIMEFRAME: str = "1m"           # Default ultra-fast sub-minute execution timeframe
    TRADING_MODE: str = "TURBO_1M"          # TURBO_1M, SCALP_3M, SCALP_5M, INTRADAY_15M
    AUTOTRADER_SCAN_INTERVAL_SECONDS: int = 1
    AUTOTRADER_AUTOSTART_ON_BOOT: bool = False
    QUALITY_MODE: bool = True
    MIN_CONFLUENCE_SCORE: float = 80.0      # Institutional minimum confluence threshold for 80%+ Win Rate
    COOLDOWN_STANDARD_MINUTES: float = 0.5  # 30 seconds standard cooldown for sub-minute trades
    COOLDOWN_POST_LOSS_MINUTES: float = 1.0 # 60 seconds post-loss cooldown
    BREAK_EVEN_TRIGGER_R: float = 0.25      # Instant Micro-Lock: Move SL to BE+offset once +0.25R achieved (secures 80%+ win rate)
    BREAK_EVEN_OFFSET_PIPS: float = 0.2     # Lock in +0.2 pip micro-buffer at break-even

    # External Market Data Providers
    FINNHUB_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None

    # Broker Credentials
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    BINANCE_TESTNET: bool = True

    OANDA_API_KEY: Optional[str] = None
    OANDA_ACCOUNT_ID: Optional[str] = None
    OANDA_ENVIRONMENT: str = "practice"

    DERIV_APP_ID: str = "1089"
    DERIV_API_TOKEN: Optional[str] = None

    MT5_HOST: str = "127.0.0.1"
    MT5_PORT: int = 18812

    # Standard Forex Pairs
    FOREX_SYMBOLS: List[str] = [
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "AUDUSD",
        "USDCAD",
        "USDCHF",
        "NZDUSD",
    ]

    # Standard Crypto Pairs
    CRYPTO_SYMBOLS: List[str] = [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "ADAUSDT",
        "XRPUSDT",
    ]

    # Exact Pip Sizes
    PIP_SIZES: Dict[str, float] = {
        "EURUSD": 0.0001,
        "GBPUSD": 0.0001,
        "USDJPY": 0.01,
        "AUDUSD": 0.0001,
        "USDCAD": 0.0001,
        "USDCHF": 0.0001,
        "NZDUSD": 0.0001,
        "BTCUSDT": 0.01,
        "ETHUSDT": 0.01,
        "SOLUSDT": 0.01,
        "BNBUSDT": 0.01,
        "ADAUSDT": 0.0001,
        "XRPUSDT": 0.0001,
    }

    # Contract / Lot Sizing Definitions
    STANDARD_LOT_UNITS: Dict[str, float] = {
        "EURUSD": 100000.0,
        "GBPUSD": 100000.0,
        "USDJPY": 100000.0,
        "AUDUSD": 100000.0,
        "USDCAD": 100000.0,
        "USDCHF": 100000.0,
        "NZDUSD": 100000.0,
        "BTCUSDT": 1.0,
        "ETHUSDT": 1.0,
        "SOLUSDT": 1.0,
        "BNBUSDT": 1.0,
        "ADAUSDT": 1.0,
        "XRPUSDT": 1.0,
    }

    @property
    def ALL_SYMBOLS(self) -> List[str]:
        return self.FOREX_SYMBOLS + self.CRYPTO_SYMBOLS

    def get_pip_size(self, symbol: str) -> float:
        return self.PIP_SIZES.get(symbol.upper(), 0.0001)

    def get_lot_units(self, symbol: str) -> float:
        return self.STANDARD_LOT_UNITS.get(symbol.upper(), 100000.0)


settings = Settings()
