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
Gestionnaire de Configuration - 100% LECTURE config.txt UNIQUEMENT
Synchronisation bidirectionnelle GUI ↔ config.txt
"""

import os
import logging
from typing import Dict, Any, List
from datetime import datetime

class ConfigManager:
    """Gestionnaire de configuration - LECTURE config.txt UNIQUEMENT"""
    
    def __init__(self, config_file: str = 'config.txt'):
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis config.txt UNIQUEMENT"""
        self.config = {}
        
        try:
            if not os.path.exists(self.config_file):
                print(f"❌ ERREUR CRITIQUE: Fichier {self.config_file} manquant !")
                print("Le bot ne peut pas fonctionner sans fichier de configuration.")
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
            
            print(f"✅ Configuration chargée: {len(self.config)} paramètres depuis config.txt")
            return self.config
            
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE lecture config.txt: {e}")
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
    
    def get(self, key: str, default=None):
        """Récupère une valeur UNIQUEMENT depuis config.txt"""
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
            'name': self.get('EXCHANGE_NAME'),
            'api_key': API_KEY,
            'secret': API_SECRET,
            'testnet': self.get('TESTNET_MODE')
        }
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Configuration Trading"""
        return {
            'simulation_mode': self.get('SIMULATION_MODE'),
            'timeframe': self.get('TIMEFRAME'),
            'auto_start': self.get('AUTO_START_BOT'),
            'max_position_size': self.get('MAX_POSITION_SIZE'),
            'max_total_exposure': self.get('MAX_TOTAL_EXPOSURE'),
            'max_daily_loss': self.get('MAX_DAILY_LOSS'),
            'stop_loss_percent': self.get('stop_loss_percent') or self.get('STOP_LOSS_PERCENT'),
            'take_profit_percent': self.get('take_profit_percent') or self.get('TAKE_PROFIT_PERCENT')
        }
    
    def get_scan_config(self) -> Dict[str, Any]:
        """Configuration Auto-scan avec critères éprouvés"""
        watchlist_raw = self.get('WATCHLIST')
        
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
            'scan_interval': self.get('SCAN_INTERVAL_MINUTES'),
            'max_cryptos': self.get('MAX_CRYPTOS'),
            
            # CRITÈRES DE SCALPING - UNIQUEMENT config.txt
            'MIN_VOLUME_BTC_ETH': self.get('min_volume_btc_eth') or self.get('MIN_VOLUME_BTC_ETH'),
            'MIN_VOLUME_ALTCOINS': self.get('min_volume_altcoins') or self.get('MIN_VOLUME_ALTCOINS'),
            'MIN_VOLUME_MICROCAPS': self.get('min_volume_microcaps') or self.get('MIN_VOLUME_MICROCAPS'),
            'VOLUME_SPIKE_THRESHOLD': self.get('VOLUME_SPIKE_THRESHOLD'),
            'MIN_PUMP_3MIN': self.get('pump_min_3min') or self.get('MIN_PUMP_3MIN'),
            'MAX_PUMP_3MIN': self.get('pump_max_3min') or self.get('MAX_PUMP_3MIN'),
            'RSI_PERIOD': self.get('RSI_PERIOD'),
            'RSI_OVERSOLD': self.get('rsi_min') or self.get('RSI_OVERSOLD'),
            'RSI_OVERBOUGHT': self.get('rsi_max') or self.get('RSI_OVERBOUGHT'),
            'EMA_FAST': self.get('ema_fast') or self.get('EMA_FAST'),
            'EMA_SLOW': self.get('ema_slow') or self.get('EMA_SLOW'),
            
            # FILTRES DE QUALITÉ - UNIQUEMENT config.txt
            'MAX_SPREAD_PERCENT': self.get('spread_max') or self.get('MAX_SPREAD_PERCENT'),
            'MIN_ORDER_BOOK_DEPTH': self.get('orderbook_depth_min') or self.get('MIN_ORDER_BOOK_DEPTH'),
            'MIN_REQUIRED_SIGNALS': self.get('signals_required') or self.get('MIN_REQUIRED_SIGNALS')
        }
    
    def get_signal_config(self) -> Dict[str, Any]:
        """Configuration Signaux"""
        return {
            'threshold': self.get('SIGNAL_THRESHOLD'),
            'min_confidence': self.get('MIN_CONFIDENCE'),
            'weights': {
                'rsi': self.get('RSI_WEIGHT'),
                'macd': self.get('MACD_WEIGHT'),
                'ema': self.get('EMA_WEIGHT'),
                'volume': self.get('VOLUME_WEIGHT'),
                'momentum': self.get('MOMENTUM_WEIGHT')
            },
            'rsi': {
                'period': self.get('RSI_PERIOD'),
                'oversold': self.get('rsi_min') or self.get('RSI_OVERSOLD'),
                'overbought': self.get('rsi_max') or self.get('RSI_OVERBOUGHT')
            },
            'macd': {
                'fast': self.get('MACD_FAST'),
                'slow': self.get('MACD_SLOW'),
                'signal': self.get('MACD_SIGNAL')
            },
            'ema': {
                'fast': self.get('ema_fast') or self.get('EMA_FAST'),
                'medium': self.get('EMA_MEDIUM'),
                'slow': self.get('ema_slow') or self.get('EMA_SLOW')
            }
        }
    
    def get_interface_config(self) -> Dict[str, Any]:
        """Configuration Interface"""
        return {
            'chart_update_seconds': self.get('CHART_UPDATE_SECONDS'),
            'log_max_lines': self.get('LOG_MAX_LINES'),
            'theme_dark': self.get('THEME_DARK')
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
        max_pos = self.get('MAX_POSITION_SIZE')
        if max_pos and not (0 < max_pos <= 1):
            errors.append("Taille position max doit être entre 0 et 1")
        
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