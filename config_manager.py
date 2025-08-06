from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
import os
load_dotenv()
api_key = API_KEY
api_secret = API_SECRET
if not api_key or not api_secret:
    raise Exception("❌ CLÉS API BINANCE MANQUANTES : le fichier .env doit contenir API_KEY et API_SECRET dans le dossier du bot.")

load_dotenv()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de Configuration - 100% sans données en dur
Synchronisation bidirectionnelle GUI ↔ config.txt
"""

import os
import logging
from typing import Dict, Any, List
from datetime import datetime

class ConfigManager:
    """Gestionnaire de configuration synchronisé avec GUI et config.txt"""
    
    def __init__(self, config_file: str = 'config.txt'):
        self.config_file = config_file
        self.config = {}
        self.default_config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis config.txt"""
        try:
            if not os.path.exists(self.config_file):
                print(f"⚠️ Fichier {self.config_file} introuvable - Création avec valeurs par défaut")
                self.create_default_config()
                return self.config
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Ignorer commentaires et lignes vides
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parser clé=valeur
                    if '=' not in line:
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Conversion automatique des types
                    self.config[key] = self._convert_value(value)
            
            print(f"✅ Configuration chargée: {len(self.config)} paramètres")
            return self.config
            
        except Exception as e:
            print(f"❌ Erreur chargement config: {e}")
            self.create_default_config()
            return self.config
    
    def _organize_config_sections(self) -> Dict[str, List[str]]:
        """Organise les paramètres de configuration par sections"""
        return {
            "CONNEXION EXCHANGE": [
                'EXCHANGE_NAME', 'API_KEY', 'API_SECRET', 'TESTNET_MODE', 'SIMULATION_MODE', 'AUTO_START_BOT'
            ],
            "FRAIS BINANCE": [
                'USE_BNB_DISCOUNT', 'BINANCE_VIP_LEVEL'
            ],
            "TIMEFRAMES": [
                'TIMEFRAME', 'CONFIRMATION_TIMEFRAME'
            ],
            "CAPITAL MANAGEMENT": [
                'INITIAL_BALANCE', 'MAX_CRYPTOS', 'POSITION_SIZE_USDT', 'order_size', 'max_open_positions'
            ],
            "SYSTÈME DE SÉCURITÉ": [
                'TRAILING_STOP_ENABLED', 'TRAILING_STOP_PERCENT', 'TRAILING_ACTIVATION_PERCENT', 
                'TIMEOUT_EXIT_SECONDS', 'STOP_LOSS_PERCENT', 'stop_loss_percent', 'trailing_start_percent', 
                'trailing_step_percent', 'timeout_seconds', 'take_profit_percent'
            ],
            "TRADING SCALPING": [
                'MAX_POSITION_SIZE', 'MAX_TOTAL_EXPOSURE', 'MAX_DAILY_LOSS', 
                'TAKE_PROFIT_PERCENT', 'RISK_REWARD_RATIO', 'max_daily_loss_percent', 'max_total_exposure'
            ],
            "AUTO-SCAN": [
                'AUTO_SCAN_ENABLED', 'SCAN_INTERVAL', 'SCAN_INTERVAL_MINUTES', 
                'SCAN_CONTINUOUS', 'MAX_SCAN_RETRIES'
            ],
            "CRITÈRES SCALPING": [
                'MIN_VOLUME_BTC_ETH', 'MIN_VOLUME_ALTCOINS', 'MIN_VOLUME_MICROCAPS',
                'VOLUME_SPIKE_THRESHOLD', 'MIN_PUMP_3MIN', 'MAX_PUMP_3MIN',
                'RSI_PERIOD', 'RSI_OVERSOLD', 'RSI_OVERBOUGHT',
                'RSI_CONFIRMATION_OVERSOLD', 'RSI_CONFIRMATION_OVERBOUGHT',
                'EMA_FAST', 'EMA_SLOW', 'min_volume_btc_eth', 'min_volume_altcoins', 'min_volume_microcaps',
                'pump_min_3min', 'pump_max_3min', 'ema_fast', 'ema_slow', 'rsi_min', 'rsi_max'
            ],
            "FILTRES QUALITÉ": [
                'MAX_SPREAD_PERCENT', 'MIN_ORDER_BOOK_DEPTH', 'MIN_REQUIRED_SIGNALS',
                'spread_max', 'orderbook_depth_min', 'signals_required'
            ],
            "FILTRAGE PAIRES": [
                'filter_suffixes', 'PAIR_SUFFIXES', 'PAIR_SUFFIX_MODE'
            ],
            "ANALYSE CHANDELLES": [
                'candle_body_ratio_min', 'candle_upper_wick_max'
            ],
            "SLIPPAGE": [
                'ENABLE_SLIPPAGE_TRACKING', 'MAX_ACCEPTABLE_SLIPPAGE'
            ],
            "OBJECTIFS": [
                'DAILY_TARGET_PERCENT', 'MAX_TRADES_PER_DAY', 'MIN_SUCCESS_RATE'
            ],
            "MODE DE FONCTIONNEMENT": [
                'simulate_trades'
            ]
        }

    def save_config(self) -> bool:
        """Sauvegarde la configuration vers config.txt"""
        try:
            # Créer une sauvegarde
            backup_file = f"{self.config_file}.backup"
            if os.path.exists(self.config_file):
                import shutil
                shutil.copy2(self.config_file, backup_file)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write("# =================================================================\n")
                f.write("# CONFIGURATION BOT DE TRADING CRYPTO - CRITÈRES ÉPROUVÉS\n")
                f.write("# Basé sur l'expérience de traders professionnels\n")
                f.write("# =================================================================\n\n")
                
                # Grouper les paramètres par section
                sections = self._organize_config_sections()
                
                for section_name, section_params in sections.items():
                    f.write(f"# {section_name}\n")
                    f.write(f"# {'=' * len(section_name)}\n")
                    
                    for key in section_params:
                        if key in self.config:
                            value = self.config[key]
                            # Convertir les listes en chaînes
                            if isinstance(value, list):
                                value = ','.join(str(v) for v in value)
                            f.write(f"{key}={value}\n")
                    
                    f.write("\n")
            
            print(f"✅ Configuration sauvegardée: {len(self.config)} paramètres")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde configuration: {e}")
            return False

    def save(self) -> bool:
        """Alias pour save_config() - Compatibilité GUI"""
        return self.save_config()
    
    def _convert_value(self, value: str) -> Any:
        """Conversion intelligente des types"""
        if not value:
            return ""
        
        # Supprimer guillemets
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        
        # Booléen
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Numérique
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Liste (virgules)
        if ',' in value and value.strip():
            return [item.strip() for item in value.split(',') if item.strip()]
        
        return value
    
    def _generate_config_content(self) -> str:
        """Génère le contenu du fichier config.txt"""
        content = []
        
        content.append("# Configuration Bot de Trading Crypto - TEMPS RÉEL")
        content.append("# Toutes les valeurs sont éditables via l'interface GUI")
        content.append(f"# Dernière sauvegarde: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        # Sections organisées
        sections = {
            "EXCHANGE & API": [
                'EXCHANGE_NAME', 'API_KEY', 'API_SECRET', 'TESTNET_MODE'
            ],
            "TRADING": [
                'SIMULATION_MODE', 'TIMEFRAME', 'AUTO_START_BOT',
                'MAX_POSITION_SIZE', 'MAX_TOTAL_EXPOSURE', 'MAX_DAILY_LOSS',
                'STOP_LOSS_PERCENT', 'TAKE_PROFIT_PERCENT'
            ],
            "AUTO-SCAN CRYPTOS": [
                'WATCHLIST', 'AUTO_SCAN_ENABLED', 'SCAN_INTERVAL_MINUTES',
                'MIN_VOLUME_USDT', 'MIN_PRICE_USDT', 'MAX_PRICE_USDT', 'MAX_CRYPTOS'
            ],
            "SIGNAUX & INDICATEURS": [
                'SIGNAL_THRESHOLD', 'MIN_CONFIDENCE',
                'RSI_WEIGHT', 'MACD_WEIGHT', 'EMA_WEIGHT', 'VOLUME_WEIGHT',
                'RSI_PERIOD', 'RSI_OVERSOLD', 'RSI_OVERBOUGHT',
                'MACD_FAST', 'MACD_SLOW', 'MACD_SIGNAL',
                'EMA_FAST', 'EMA_MEDIUM', 'EMA_SLOW'
            ],
            "INTERFACE": [
                'CHART_UPDATE_SECONDS', 'LOG_MAX_LINES', 'THEME_DARK'
            ]
        }
        
        for section_name, keys in sections.items():
            content.append(f"# {section_name}")
            content.append("# " + "=" * len(section_name))
            
            for key in keys:
                value = self.config.get(key, self.get_default_value(key))
                content.append(f"{key}={value}")
            
            content.append("")
        
        return "\n".join(content)
    
    def create_default_config(self):
        """Crée une configuration par défaut"""
        self.config = {
            # Exchange
            'EXCHANGE_NAME': 'binance',
            'API_KEY': '',
            'API_SECRET': '',
            'TESTNET_MODE': False,
            
            # Trading
            'SIMULATION_MODE': True,
            'TIMEFRAME': '1h',
            'AUTO_START_BOT': True,
            'MAX_POSITION_SIZE': self.get('MAX_POSITION_SIZE', 0.05),
            'MAX_TOTAL_EXPOSURE': self.get('MAX_TOTAL_EXPOSURE', 0.20),
            'MAX_DAILY_LOSS': self.get('MAX_DAILY_LOSS', 0.05),
            'STOP_LOSS_PERCENT': self.get('STOP_LOSS_PERCENT', 2.0),
            'TAKE_PROFIT_PERCENT': self.get('TAKE_PROFIT_PERCENT', 6.0),
            
            # Capital management à partir du config.txt
            'order_size': self.get('order_size', 50),
            'max_open_positions': self.get('max_open_positions', 2),
            'stop_loss_percent': self.get('stop_loss_percent', 0.5),
            'trailing_start_percent': self.get('trailing_start_percent', 0.8),
            'trailing_step_percent': self.get('trailing_step_percent', 0.3),
            'timeout_seconds': self.get('timeout_seconds', 180),
            'take_profit_percent': self.get('take_profit_percent', 0.8),
            
            # Indicateurs techniques à partir du config.txt
            'ema_fast': self.get('ema_fast', 8),
            'ema_slow': self.get('ema_slow', 20),
            'rsi_min': self.get('rsi_min', 28),
            'rsi_max': self.get('rsi_max', 72),
            
            # Critères de scalping à partir du config.txt
            'pump_min_3min': self.get('pump_min_3min', 1.2),
            'pump_max_3min': self.get('pump_max_3min', 2.5),
            'min_volume_btc_eth': self.get('min_volume_btc_eth', 70000000),
            'min_volume_altcoins': self.get('min_volume_altcoins', 12000000),
            'min_volume_microcaps': self.get('min_volume_microcaps', 2000000),
            'spread_max': self.get('spread_max', 0.08),
            'orderbook_depth_min': self.get('orderbook_depth_min', 100),
            'signals_required': self.get('signals_required', 3),
            
            # Filtrage des paires à partir du config.txt
            'filter_suffixes': self.get('filter_suffixes', 'USDT,BTC'),
            'candle_body_ratio_min': self.get('candle_body_ratio_min', 0.65),
            'candle_upper_wick_max': self.get('candle_upper_wick_max', 0.25),
            
            # Gestion des risques à partir du config.txt
            'max_daily_loss_percent': self.get('max_daily_loss_percent', 3),
            'max_total_exposure': self.get('max_total_exposure', 1000),
            'simulate_trades': self.get('simulate_trades', False),
            
            # Auto-scan
            'WATCHLIST': '',  # Vide = auto-scan
            'AUTO_SCAN_ENABLED': True,
            'SCAN_INTERVAL_MINUTES': self.get('SCAN_INTERVAL_MINUTES', 5),
            'MIN_VOLUME_USDT': self.get('MIN_VOLUME_USDT', 5000000),
            'MIN_PRICE_USDT': self.get('MIN_PRICE_USDT', 0.001),
            'MAX_PRICE_USDT': self.get('MAX_PRICE_USDT', 50000),
            'MAX_CRYPTOS': self.get('MAX_CRYPTOS', 5),
            
            # Signaux
            'SIGNAL_THRESHOLD': self.get('SIGNAL_THRESHOLD', 35),
            'MIN_CONFIDENCE': self.get('MIN_CONFIDENCE', 0.6),
            'RSI_WEIGHT': self.get('RSI_WEIGHT', 25),
            'MACD_WEIGHT': self.get('MACD_WEIGHT', 30),
            'EMA_WEIGHT': self.get('EMA_WEIGHT', 25),
            'VOLUME_WEIGHT': self.get('VOLUME_WEIGHT', 10),
            'MOMENTUM_WEIGHT': self.get('MOMENTUM_WEIGHT', 10),
            'RSI_PERIOD': self.get('RSI_PERIOD', 14),
            'RSI_OVERSOLD': self.get('RSI_OVERSOLD', 30),
            'RSI_OVERBOUGHT': self.get('RSI_OVERBOUGHT', 70),
            'MACD_FAST': self.get('MACD_FAST', 12),
            'MACD_SLOW': self.get('MACD_SLOW', 26),
            'MACD_SIGNAL': self.get('MACD_SIGNAL', 9),
            'EMA_FAST': self.get('EMA_FAST', 9),
            'EMA_MEDIUM': self.get('EMA_MEDIUM', 21),
            'EMA_SLOW': self.get('EMA_SLOW', 50),
            
            # Configuration avancée
            'CHART_UPDATE_SECONDS': self.get('CHART_UPDATE_SECONDS', 1),
            'LOG_MAX_LINES': self.get('LOG_MAX_LINES', 100),
            'THEME_DARK': self.get('THEME_DARK', True),
            
            # Configuration REST API
            'USE_REST_FALLBACK': self.get('USE_REST_FALLBACK', True),
            'REST_UPDATE_INTERVAL': self.get('REST_UPDATE_INTERVAL', 5),
            'MAX_REST_REQUESTS_PER_MINUTE': self.get('MAX_REST_REQUESTS_PER_MINUTE', 1200),
            'REST_TIMEOUT': self.get('REST_TIMEOUT', 10),
            'AUTO_START_BOT': True,
            
            # Sélection des paires
            'QUOTE_CURRENCIES': self.get('QUOTE_CURRENCIES', 'USDT BUSD BTC ETH BNB'),
            'DEFAULT_QUOTE_CURRENCY': self.get('DEFAULT_QUOTE_CURRENCY', 'USDT'),
            
            # Nouveaux paramètres scalping configurables
            'MIN_VOLUME_24H': self.get('MIN_VOLUME_24H', 2000000),
            'MIN_PUMP_3MIN': self.get('MIN_PUMP_3MIN', 0.5),
            'MIN_AMPLITUDE_5CANDLES': self.get('MIN_AMPLITUDE_5CANDLES', 0.8),
            'RSI_PERIOD_SCALPING': self.get('RSI_PERIOD_SCALPING', 14),
            'RSI_MIN_SCALPING': self.get('RSI_MIN_SCALPING', 40),
            'RSI_MAX_SCALPING': self.get('RSI_MAX_SCALPING', 80),
            'EMA_FAST_SCALPING': self.get('EMA_FAST_SCALPING', 9),
            'EMA_SLOW_SCALPING': self.get('EMA_SLOW_SCALPING', 21),
            'MIN_VOLUME_RATIO_CANDLE': self.get('MIN_VOLUME_RATIO_CANDLE', 1.2),
            'MAX_SPREAD_PERCENT': self.get('MAX_SPREAD_PERCENT', 0.3),
            'MAX_ORDERBOOK_WALL_RATIO': self.get('MAX_ORDERBOOK_WALL_RATIO', 3.0),
            'MIN_GREEN_CANDLES': self.get('MIN_GREEN_CANDLES', 1),
            'MIN_DELTA_VOLUME_PERCENT': self.get('MIN_DELTA_VOLUME_PERCENT', 20),
            
            # Configuration VIP et BNB
            'USE_BNB_DISCOUNT': self.get('USE_BNB_DISCOUNT', True),
            'BINANCE_VIP_LEVEL': self.get('BINANCE_VIP_LEVEL', 0),
            
            # Nouveaux paramètres pour correspondre aux valeurs du config.txt
            'MIN_VOLUME_BTC_ETH': self.get('min_volume_btc_eth', 70000000),
            'MIN_VOLUME_ALTCOINS': self.get('min_volume_altcoins', 12000000),
            'MIN_VOLUME_MICROCAPS': self.get('min_volume_microcaps', 2000000),
            'VOLUME_SPIKE_THRESHOLD': self.get('VOLUME_SPIKE_THRESHOLD', 130),
            'MIN_REQUIRED_SIGNALS': self.get('signals_required', 3),
            'MIN_ORDER_BOOK_DEPTH': self.get('orderbook_depth_min', 100),
            'PAIR_SUFFIXES': self.get('filter_suffixes', 'USDT,BTC'),
            'PAIR_SUFFIX_MODE': self.get('PAIR_SUFFIX_MODE', 'INCLUDE'),
            'TRAILING_STOP_ENABLED': self.get('TRAILING_STOP_ENABLED', True),
            'TRAILING_STOP_PERCENT': self.get('trailing_step_percent', 0.3),
            'TRAILING_ACTIVATION_PERCENT': self.get('trailing_start_percent', 0.8),
            'TIMEOUT_EXIT_SECONDS': self.get('timeout_seconds', 180),
            'INITIAL_BALANCE': self.get('INITIAL_BALANCE', 1000.0),
            'POSITION_SIZE_USDT': self.get('order_size', 50),
            'RISK_REWARD_RATIO': self.get('RISK_REWARD_RATIO', 2.0),
            'DAILY_TARGET_PERCENT': self.get('DAILY_TARGET_PERCENT', 2.0),
            'MAX_TRADES_PER_DAY': self.get('MAX_TRADES_PER_DAY', 20),
            'MIN_SUCCESS_RATE': self.get('MIN_SUCCESS_RATE', 60),
            'ENABLE_SLIPPAGE_TRACKING': self.get('ENABLE_SLIPPAGE_TRACKING', True),
            'MAX_ACCEPTABLE_SLIPPAGE': self.get('MAX_ACCEPTABLE_SLIPPAGE', 0.1),
            
            # Synchroniser avec les valeurs courantes du config.txt
            'MAX_PUMP_3MIN': self.get('pump_max_3min', 2.5),
            'RSI_CONFIRMATION_OVERSOLD': self.get('rsi_min', 28),
            'RSI_CONFIRMATION_OVERBOUGHT': self.get('rsi_max', 72)
        }
        
        self.save_config()
    
    def get_default_value(self, key: str) -> Any:
        """Retourne la valeur par défaut d'une clé"""
        defaults = {
            'EXCHANGE_NAME': 'binance',
            'API_KEY': '',
            'API_SECRET': '',
            'TESTNET_MODE': False,
            'SIMULATION_MODE': True,
            'TIMEFRAME': '1h',
            'AUTO_START_BOT': True,
            'MAX_POSITION_SIZE': 0.05,
            'MAX_TOTAL_EXPOSURE': 0.20,
            'MAX_DAILY_LOSS': 0.05,
            'STOP_LOSS_PERCENT': 2.0,
            'TAKE_PROFIT_PERCENT': 6.0,
            'WATCHLIST': '',
            'AUTO_SCAN_ENABLED': True,
            'SCAN_INTERVAL_MINUTES': 5,
            'MIN_VOLUME_USDT': 5000000,
            'MIN_PRICE_USDT': 0.001,
            'MAX_PRICE_USDT': 50000,
            'MAX_CRYPTOS': 5,
            'SIGNAL_THRESHOLD': 35,
            'MIN_CONFIDENCE': 0.6,
            'RSI_WEIGHT': 25,
            'MACD_WEIGHT': 30,
            'EMA_WEIGHT': 25,
            'VOLUME_WEIGHT': 10,
            'MOMENTUM_WEIGHT': 10,
            'RSI_PERIOD': 14,
            'RSI_OVERSOLD': 30,
            'RSI_OVERBOUGHT': 70,
            'MACD_FAST': 12,
            'MACD_SLOW': 26,
            'MACD_SIGNAL': 9,
            'EMA_FAST': 9,
            'EMA_MEDIUM': 21,
            'EMA_SLOW': 50,
            'CHART_UPDATE_SECONDS': 1,
            'LOG_MAX_LINES': 100,
            'THEME_DARK': True,
            # Sélection des paires
            'QUOTE_CURRENCIES': 'USDT BUSD BTC ETH BNB',
            'DEFAULT_QUOTE_CURRENCY': 'USDT',
            # Paramètres scalping configurables
            'MIN_VOLUME_24H': 2000000,
            'MIN_PUMP_3MIN': 0.5,
            'MIN_AMPLITUDE_5CANDLES': 0.8,
            'RSI_PERIOD_SCALPING': 14,
            'RSI_MIN_SCALPING': 40,
            'RSI_MAX_SCALPING': 80,
            'EMA_FAST_SCALPING': 9,
            'EMA_SLOW_SCALPING': 21,
            'MIN_VOLUME_RATIO_CANDLE': 1.2,
            'MAX_SPREAD_PERCENT': 0.3,
            'MAX_ORDERBOOK_WALL_RATIO': 3.0,
            'MIN_GREEN_CANDLES': 1,
            'MIN_DELTA_VOLUME_PERCENT': 20,
            # Configuration VIP et BNB
            'USE_BNB_DISCOUNT': True,
            'BINANCE_VIP_LEVEL': 0,
            # Paramètres du config.txt
            'order_size': 50,
            'max_open_positions': 2,
            'stop_loss_percent': 0.5,
            'trailing_start_percent': 0.8,
            'trailing_step_percent': 0.3,
            'timeout_seconds': 180,
            'take_profit_percent': 0.8,
            'ema_fast': 8,
            'ema_slow': 20,
            'rsi_min': 28,
            'rsi_max': 72,
            'pump_min_3min': 1.2,
            'pump_max_3min': 2.5,
            'min_volume_btc_eth': 70000000,
            'min_volume_altcoins': 12000000,
            'min_volume_microcaps': 2000000,
            'spread_max': 0.08,
            'orderbook_depth_min': 100,
            'signals_required': 3,
            'filter_suffixes': 'USDT,BTC',
            'candle_body_ratio_min': 0.65,
            'candle_upper_wick_max': 0.25,
            'max_daily_loss_percent': 3,
            'max_total_exposure': 1000,
            'simulate_trades': False
        }
        return defaults.get(key, '')
    
    def get(self, key: str, default=None):
        """Récupère une valeur"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Définit une valeur"""
        self.config[key] = value
    
    def update_from_gui(self, gui_values: Dict[str, Any]):
        """Met à jour la config depuis l'interface GUI"""
        for key, value in gui_values.items():
            self.config[key] = value
    
    def get_exchange_config(self) -> Dict[str, Any]:
        """Configuration Exchange"""
        return {
            'name': self.get('EXCHANGE_NAME', 'binance'),
            'api_key': API_KEY,
            'secret': API_SECRET,
            'testnet': self.get('TESTNET_MODE', False)
        }
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Configuration Trading"""
        return {
            'simulation_mode': self.get('SIMULATION_MODE', True),
            'timeframe': self.get('TIMEFRAME', '1h'),
            'auto_start': self.get('AUTO_START_BOT', True),
            'max_position_size': self.get('MAX_POSITION_SIZE', 0.05),
            'max_total_exposure': self.get('MAX_TOTAL_EXPOSURE', 0.20),
            'max_daily_loss': self.get('MAX_DAILY_LOSS', 0.05),
            'stop_loss_percent': self.get('stop_loss_percent', self.get('STOP_LOSS_PERCENT', 2.0)),
            'take_profit_percent': self.get('take_profit_percent', self.get('TAKE_PROFIT_PERCENT', 6.0))
        }
    
    def get_scan_config(self) -> Dict[str, Any]:
        """Configuration Auto-scan avec critères éprouvés"""
        watchlist_raw = self.get('WATCHLIST', '')
        
        # Si watchlist vide = auto-scan
        if not watchlist_raw or str(watchlist_raw).strip() == '':
            watchlist = []
        elif isinstance(watchlist_raw, list):
            watchlist = [pair.strip() for pair in watchlist_raw if pair.strip()]
        else:
            watchlist = [pair.strip() for pair in str(watchlist_raw).split(',') if pair.strip()]
        
        return {
            'watchlist': watchlist,
            'auto_scan_enabled': len(watchlist) == 0,  # Auto-scan si liste vide
            'scan_interval': self.get('SCAN_INTERVAL_MINUTES', 1),
            'max_cryptos': self.get('MAX_CRYPTOS', 20),
            
            # CRITÈRES ÉPROUVÉS DE SCALPING - utiliser config.txt si disponible
            'MIN_VOLUME_BTC_ETH': self.get('min_volume_btc_eth', self.get('MIN_VOLUME_BTC_ETH', 70000000)),
            'MIN_VOLUME_ALTCOINS': self.get('min_volume_altcoins', self.get('MIN_VOLUME_ALTCOINS', 12000000)),
            'MIN_VOLUME_MICROCAPS': self.get('min_volume_microcaps', self.get('MIN_VOLUME_MICROCAPS', 2000000)),
            'VOLUME_SPIKE_THRESHOLD': self.get('VOLUME_SPIKE_THRESHOLD', 130),
            'MIN_PUMP_3MIN': self.get('pump_min_3min', self.get('MIN_PUMP_3MIN', 1.2)),
            'MAX_PUMP_3MIN': self.get('pump_max_3min', self.get('MAX_PUMP_3MIN', 2.5)),
            'RSI_PERIOD': self.get('RSI_PERIOD', 14),
            'RSI_OVERSOLD': self.get('rsi_min', self.get('RSI_OVERSOLD', 28)),
            'RSI_OVERBOUGHT': self.get('rsi_max', self.get('RSI_OVERBOUGHT', 72)),
            'EMA_FAST': self.get('ema_fast', self.get('EMA_FAST', 8)),
            'EMA_SLOW': self.get('ema_slow', self.get('EMA_SLOW', 20)),
            
            # FILTRES DE QUALITÉ AVANCÉS - utiliser config.txt si disponible
            'MAX_SPREAD_PERCENT': self.get('spread_max', self.get('MAX_SPREAD_PERCENT', 0.08)),
            'MIN_ORDER_BOOK_DEPTH': self.get('orderbook_depth_min', self.get('MIN_ORDER_BOOK_DEPTH', 100)),
            'MIN_REQUIRED_SIGNALS': self.get('signals_required', self.get('MIN_REQUIRED_SIGNALS', 3))
        }
    
    def get_signal_config(self) -> Dict[str, Any]:
        """Configuration Signaux"""
        return {
            'threshold': self.get('SIGNAL_THRESHOLD', 35),
            'min_confidence': self.get('MIN_CONFIDENCE', 0.6),
            'weights': {
                'rsi': self.get('RSI_WEIGHT', 25),
                'macd': self.get('MACD_WEIGHT', 30),
                'ema': self.get('EMA_WEIGHT', 25),
                'volume': self.get('VOLUME_WEIGHT', 10),
                'momentum': self.get('MOMENTUM_WEIGHT', 10)
            },
            'rsi': {
                'period': self.get('RSI_PERIOD', 14),
                'oversold': self.get('rsi_min', self.get('RSI_OVERSOLD', 30)),
                'overbought': self.get('rsi_max', self.get('RSI_OVERBOUGHT', 70))
            },
            'macd': {
                'fast': self.get('MACD_FAST', 12),
                'slow': self.get('MACD_SLOW', 26),
                'signal': self.get('MACD_SIGNAL', 9)
            },
            'ema': {
                'fast': self.get('ema_fast', self.get('EMA_FAST', 9)),
                'medium': self.get('EMA_MEDIUM', 21),
                'slow': self.get('ema_slow', self.get('EMA_SLOW', 50))
            }
        }
    
    def get_interface_config(self) -> Dict[str, Any]:
        """Configuration Interface"""
        return {
            'chart_update_seconds': self.get('CHART_UPDATE_SECONDS', 1),
            'log_max_lines': self.get('LOG_MAX_LINES', 100),
            'theme_dark': self.get('THEME_DARK', True)
        }
    
    def validate_config(self) -> List[str]:
        """Valide la configuration et retourne les erreurs"""
        errors = []
        
        # Validation Exchange
        if not API_KEY:
            errors.append("Clé API manquante")
        if not API_SECRET:
            errors.append("Clé secrète manquante")
        
        # Validation Trading
        max_pos = self.get('MAX_POSITION_SIZE', 0)
        if not 0 < max_pos <= 1:
            errors.append("Taille position max doit être entre 0 et 1")
        
        # Validation Poids
        total_weight = (self.get('RSI_WEIGHT', 0) + self.get('MACD_WEIGHT', 0) + 
                       self.get('EMA_WEIGHT', 0) + self.get('VOLUME_WEIGHT', 0) + self.get('MOMENTUM_WEIGHT', 0))
        if total_weight != 100:
            errors.append(f"Total des poids doit être 100 (actuel: {total_weight})")
        
        return errors
    
    def is_valid(self) -> bool:
        """Vérifie si la configuration est valide"""
        return len(self.validate_config()) == 0

# Test du gestionnaire
if __name__ == "__main__":
    print("🔧 Test du gestionnaire de configuration")
    
    config = ConfigManager()
    
    # Test de validation
    errors = config.validate_config()
    if errors:
        print("❌ Erreurs:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Configuration valide")
    
    # Test des getters
    print(f"\n📡 Exchange: {config.get_exchange_config()}")
    print(f"📈 Trading: {config.get_trading_config()}")
    print(f"🔍 Scan: {config.get_scan_config()}")
    print(f"🎯 Signaux: {config.get_signal_config()}")