from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
import os
from dotenv import load_dotenv
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
                'INITIAL_BALANCE', 'MAX_CRYPTOS', 'POSITION_SIZE_USDT'
            ],
            "SYSTÈME DE SÉCURITÉ": [
                'TRAILING_STOP_ENABLED', 'TRAILING_STOP_PERCENT', 'TRAILING_ACTIVATION_PERCENT', 
                'TIMEOUT_EXIT_SECONDS', 'STOP_LOSS_PERCENT'
            ],
            "TRADING SCALPING": [
                'MAX_POSITION_SIZE', 'MAX_TOTAL_EXPOSURE', 'MAX_DAILY_LOSS', 
                'TAKE_PROFIT_PERCENT', 'RISK_REWARD_RATIO'
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
                'EMA_FAST', 'EMA_SLOW'
            ],
            "FILTRES QUALITÉ": [
                'MAX_SPREAD_PERCENT', 'MIN_ORDER_BOOK_DEPTH', 'MIN_REQUIRED_SIGNALS'
            ],
            "SLIPPAGE": [
                'ENABLE_SLIPPAGE_TRACKING', 'MAX_ACCEPTABLE_SLIPPAGE'
            ],
            "OBJECTIFS": [
                'DAILY_TARGET_PERCENT', 'MAX_TRADES_PER_DAY', 'MIN_SUCCESS_RATE'
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
            'MAX_POSITION_SIZE': 0.05,
            'MAX_TOTAL_EXPOSURE': 0.20,
            'MAX_DAILY_LOSS': 0.05,
            'STOP_LOSS_PERCENT': 2.0,
            'TAKE_PROFIT_PERCENT': 6.0,
            
            # Auto-scan
            'WATCHLIST': '',  # Vide = auto-scan
            'AUTO_SCAN_ENABLED': True,
            'SCAN_INTERVAL_MINUTES': 5,
            'MIN_VOLUME_USDT': 5000000,
            'MIN_PRICE_USDT': 0.001,
            'MAX_PRICE_USDT': 50000,
            'MAX_CRYPTOS': 5,
            
            # Signaux
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
            
            # Configuration avancée
            'CHART_UPDATE_SECONDS': 1,
            'LOG_MAX_LINES': 100,
            'THEME_DARK': True,
            
            # Configuration REST API
            'USE_REST_FALLBACK': True,
            'REST_UPDATE_INTERVAL': 5,
            'MAX_REST_REQUESTS_PER_MINUTE': 1200,
            'REST_TIMEOUT': 10,
            'AUTO_START_BOT': True,
            
            # Sélection des paires
            'QUOTE_CURRENCIES': 'USDT BUSD BTC ETH BNB',
            'DEFAULT_QUOTE_CURRENCY': 'USDT',
            
            # Nouveaux paramètres scalping configurables
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
            'BINANCE_VIP_LEVEL': 0
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
            'BINANCE_VIP_LEVEL': 0
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
            'stop_loss_percent': self.get('STOP_LOSS_PERCENT', 2.0),
            'take_profit_percent': self.get('TAKE_PROFIT_PERCENT', 6.0)
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
            
            # CRITÈRES ÉPROUVÉS DE SCALPING
            'MIN_VOLUME_BTC_ETH': self.get('MIN_VOLUME_BTC_ETH', 50_000_000),
            'MIN_VOLUME_ALTCOINS': self.get('MIN_VOLUME_ALTCOINS', 8_000_000),
            'MIN_VOLUME_MICROCAPS': self.get('MIN_VOLUME_MICROCAPS', 1_000_000),
            'VOLUME_SPIKE_THRESHOLD': self.get('VOLUME_SPIKE_THRESHOLD', 130),
            'MIN_PUMP_3MIN': self.get('MIN_PUMP_3MIN', 0.8),
            'MAX_PUMP_3MIN': self.get('MAX_PUMP_3MIN', 2.0),
            'RSI_PERIOD': self.get('RSI_PERIOD', 14),
            'RSI_OVERSOLD': self.get('RSI_OVERSOLD', 25),
            'RSI_OVERBOUGHT': self.get('RSI_OVERBOUGHT', 75),
            'EMA_FAST': self.get('EMA_FAST', 9),
            'EMA_SLOW': self.get('EMA_SLOW', 21),
            
            # FILTRES DE QUALITÉ AVANCÉS
            'MAX_SPREAD_PERCENT': self.get('MAX_SPREAD_PERCENT', 0.1),
            'MIN_ORDER_BOOK_DEPTH': self.get('MIN_ORDER_BOOK_DEPTH', 50),
            'MIN_REQUIRED_SIGNALS': self.get('MIN_REQUIRED_SIGNALS', 2)
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
                'oversold': self.get('RSI_OVERSOLD', 30),
                'overbought': self.get('RSI_OVERBOUGHT', 70)
            },
            'macd': {
                'fast': self.get('MACD_FAST', 12),
                'slow': self.get('MACD_SLOW', 26),
                'signal': self.get('MACD_SIGNAL', 9)
            },
            'ema': {
                'fast': self.get('EMA_FAST', 9),
                'medium': self.get('EMA_MEDIUM', 21),
                'slow': self.get('EMA_SLOW', 50)
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