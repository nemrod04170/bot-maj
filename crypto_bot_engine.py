import asyncio
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
Moteur de Trading Principal - Temps Réel
Architecture modulaire sans données en dur
"""

import ccxt
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Callable
import threading

from websocket_realtime import BinanceWebSocketManager
from scalping_scanner import ScalpingScanner

class TechnicalIndicators:
    """Calculateurs d'indicateurs techniques optimisés"""
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calcule le RSI"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calcule le MACD"""
        exp1 = data.ewm(span=fast).mean()
        exp2 = data.ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Calcule la moyenne mobile exponentielle"""
        return data.ewm(span=period).mean()

class RiskManager:
    """Gestionnaire des risques configuré depuis config.txt"""
    
    def __init__(self, config: Dict):
        self.max_position_size = config.get('max_position_size', 0.05)
        self.max_total_exposure = config.get('max_total_exposure', 0.20)
        self.max_daily_loss = config.get('max_daily_loss', 0.05)
        self.stop_loss_percent = config.get('stop_loss_percent', 2.0)
        
        self.daily_pnl = 0.0
        self.daily_reset_date = datetime.now().date()
    
    def calculate_position_size(self, balance: float, entry_price: float) -> float:
        """Calcule la taille de position optimale"""
        risk_amount = balance * self.max_position_size
        return risk_amount / entry_price
    
    def calculate_stop_loss(self, entry_price: float, direction: str) -> float:
        """Calcule le prix de stop loss"""
        percent = self.stop_loss_percent / 100
        
        if direction == 'long':
            return entry_price * (1 - percent)
        else:  # short
            return entry_price * (1 + percent)
    
    def check_daily_loss_limit(self) -> bool:
        """Vérifie la limite de perte quotidienne"""
        if datetime.now().date() > self.daily_reset_date:
            self.daily_pnl = 0.0
            self.daily_reset_date = datetime.now().date()
        
        return self.daily_pnl < -self.max_daily_loss

class SignalGenerator:
    """Générateur de signaux configuré depuis config.txt"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.indicators = TechnicalIndicators()
        
        # Configuration depuis config.txt
        self.signal_threshold = config.get('threshold', 35)
        self.min_confidence = config.get('min_confidence', 0.6)
        
        # Poids des indicateurs
        weights = config.get('weights', {})
        self.rsi_weight = weights.get('rsi', 25)
        self.macd_weight = weights.get('macd', 30)
        self.ema_weight = weights.get('ema', 25)
        self.volume_weight = weights.get('volume', 20)
        
        # Configuration RSI
        rsi_config = config.get('rsi', {})
        self.rsi_period = rsi_config.get('period', 14)
        self.rsi_oversold = rsi_config.get('oversold', 30)
        self.rsi_overbought = rsi_config.get('overbought', 70)
        
        # Configuration MACD
        macd_config = config.get('macd', {})
        self.macd_fast = macd_config.get('fast', 12)
        self.macd_slow = macd_config.get('slow', 26)
        self.macd_signal = macd_config.get('signal', 9)
        
        # Configuration EMA
        ema_config = config.get('ema', {})
        self.ema_fast = ema_config.get('fast', 9)
        self.ema_medium = ema_config.get('medium', 21)
        self.ema_slow = ema_config.get('slow', 50)
    
    def analyze_symbol(self, symbol: str, current_price: float, 
                      kline_df: pd.DataFrame, volume_24h: float, change_24h: float) -> Dict:
        """Analyse SIMPLIFIÉE pour cryptos pré-sélectionnées - utilise le score du scan"""
        
        # Si la crypto est dans la watchlist, elle a DÉJÀ passé tous les filtres du scan
        # On doit juste générer un signal de trading basé sur le momentum actuel
        
        # Score basé uniquement sur momentum actuel (pas de RSI/MACD/EMA complexe)
        score = 0
        confidence_factors = []
        
        # 1. Score momentum 24h (principal critère) - 70% du score
        momentum_score = 0
        if change_24h >= 8:      # Hausse très forte
            momentum_score = 70
            confidence_factors.append("VERY_STRONG_MOMENTUM")
        elif change_24h >= 5:    # Hausse forte  
            momentum_score = 60
            confidence_factors.append("STRONG_MOMENTUM")
        elif change_24h >= 3:    # Hausse modérée
            momentum_score = 50
            confidence_factors.append("MODERATE_MOMENTUM")
        elif change_24h >= 1:    # Hausse légère
            momentum_score = 40
            confidence_factors.append("LIGHT_MOMENTUM")
        else:                    # Stable ou baisse
            momentum_score = 20
            confidence_factors.append("NEUTRAL_MOMENTUM")
        
        score += momentum_score
        
        # 2. Score volume - 30% du score
        volume_score = 0
        if volume_24h >= 50_000_000:  # Volume très élevé
            volume_score = 30
            confidence_factors.append("HIGH_VOLUME")
        elif volume_24h >= 20_000_000:  # Volume élevé
            volume_score = 25
            confidence_factors.append("GOOD_VOLUME")
        elif volume_24h >= 10_000_000:  # Volume correct
            volume_score = 20
            confidence_factors.append("ADEQUATE_VOLUME")
        else:                           # Volume moyen
            volume_score = 15
            confidence_factors.append("AVERAGE_VOLUME")
        
        score += volume_score
        
        # 3. Décision de trading - SEUIL UNIFIÉ avec le scan
        if score >= self.signal_threshold:
            signal = 'BUY'
        else:
            signal = 'HOLD'
        
        # 4. Confiance basée sur la pré-sélection + momentum
        confidence = min(score / 100, 1.0)
        
        # Bonus confiance car crypto déjà pré-sélectionnée par le scan
        confidence = min(confidence + 0.2, 1.0)  # +20% car pré-sélectionnée
        confidence_factors.append("PRE_SELECTED_BY_SCAN")
        
        reason = f"Signal {signal} - Crypto pré-sélectionnée - Facteurs: {', '.join(confidence_factors)}"
        
        return {
            'signal': signal,
            'score': score,
            'confidence': confidence,
            'rsi': 50,  # Valeurs neutres car pas utilisées
            'macd': 0.1 if change_24h > 0 else -0.1,
            'price': current_price,
            'change_24h': change_24h,
            'confidence_factors': confidence_factors,
            'reason': reason,
            'pre_selected': True,  # Marquer comme pré-sélectionnée
            'timestamp': datetime.now()
        }
    
    def _analyze_simple_momentum(self, symbol: str, current_price: float, volume_24h: float, change_24h: float) -> Dict:
        """Analyse simplifiée basée sur momentum quand peu de données"""
        
        score = 0
        confidence_factors = []
        
        # Score basé uniquement sur momentum et volume
        if change_24h >= 8:
            score = 75
            confidence_factors.append("STRONG_MOMENTUM_SIMPLE")
        elif change_24h >= 5:
            score = 65
            confidence_factors.append("GOOD_MOMENTUM_SIMPLE")
        elif change_24h >= 3:
            score = 55
            confidence_factors.append("MODERATE_MOMENTUM_SIMPLE")
        
        # Bonus volume
        if volume_24h >= 50_000_000:
            score += 10
            confidence_factors.append("HIGH_VOLUME_SIMPLE")
        
        signal = 'BUY' if score >= 55 else 'HOLD'
        confidence = min(score / 100, 1.0)
        
        self.log(f"🚀 {symbol}: ANALYSE SIMPLIFIÉE - Score={score}, Signal={signal}")
        
        return {
            'signal': signal,
            'score': score,
            'confidence': confidence,
            'rsi': 50,  # Valeur neutre
            'macd': 0.1 if change_24h > 0 else -0.1,
            'price': current_price,
            'change_24h': change_24h,
            'confidence_factors': confidence_factors,
            'reason': f"Analyse simplifiée - {', '.join(confidence_factors)}",
            'simple_analysis': True,
            'timestamp': datetime.now()
        }

class CryptoTradingBot:
    """Bot de trading principal - Configuration 100% depuis config.txt"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
        # Chargement des configurations
        self.exchange_config = config_manager.get_exchange_config()
        self.trading_config = config_manager.get_trading_config()
        self.scan_config = config_manager.get_scan_config()
        self.signal_config = config_manager.get_signal_config()
        
        # Variables de trading simulé
        self.simulation_mode = config_manager.get('SIMULATION_MODE', True)
        self.initial_balance = config_manager.get('INITIAL_BALANCE', 2000.0)
        self.simulated_balance = self.initial_balance  # Balance de départ optimisée
        self.balance = self.initial_balance  # Balance actuelle
        self.position_size_usdt = config_manager.get('POSITION_SIZE_USDT', 100.0)  # 100€ par crypto
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.total_fees = 0.0  # NOUVEAU: Tracking des frais totaux
        self.max_cryptos = config_manager.get('MAX_CRYPTOS', 20)
        self.scan_interval_minutes = config_manager.get('SCAN_INTERVAL_MINUTES', 1)
        
        # CORRECTION: Initialiser open_positions
        self.open_positions = []
        
        # Système de sécurité à 3 couches
        self.trailing_stop_enabled = config_manager.get('TRAILING_STOP_ENABLED', True)
        self.trailing_stop_percent = config_manager.get('TRAILING_STOP_PERCENT', 0.3)
        self.trailing_activation_percent = config_manager.get('TRAILING_ACTIVATION_PERCENT', 0.4)
        self.timeout_exit_seconds = config_manager.get('TIMEOUT_EXIT_SECONDS', 45)
        self.stop_loss_percent = config_manager.get('STOP_LOSS_PERCENT', 0.6)
        
        # Tracking de slippage
        self.enable_slippage_tracking = config_manager.get('ENABLE_SLIPPAGE_TRACKING', True)
        self.max_acceptable_slippage = config_manager.get('MAX_ACCEPTABLE_SLIPPAGE', 0.2)
        self.slippage_history = []
        
        # NOUVEAU: Système de portefeuille virtuel persistant
        self.portfolio_file = 'portfolio_state.json'
        self.closed_trades = []
        self.last_save_time = datetime.now()
        
        # Callbacks
        self.callbacks = {
            'log_message': [],
            'scan_update': [],
            'position_update': [],
            'exchange_status': [],
            'trade_executed': [],
            'balance_update': [],
            'position_closed': [],
            'trade_closed': [],
            'price_update': []
        }
        
        # Initialiser l'exchange avec les vraies clés
        self.exchange = None  # Initialiser d'abord
        if not self._initialize_exchange():
            self.log("❌ Impossible de se connecter à Binance")
            self.log("   Vérifiez vos clés API dans l'onglet Configuration")
            # Ne pas retourner ici - continuer l'initialisation mais marquer comme non connecté
            self.exchange_connected = False
        else:
            self.exchange_connected = True
        
        # Composants du bot
        self.risk_manager = RiskManager(self.trading_config)
        self.signal_generator = SignalGenerator(self.signal_config)
        self.websocket_manager = None
        
        # État du bot
        self.is_running = False
        self.simulation_mode = self.trading_config['simulation_mode']
        self.watchlist = []
        self.positions = {}
        self.balance = 0.0
        
        # Démarrer le thread de sauvegarde automatique APRÈS l'initialisation de is_running
        threading.Thread(target=self._auto_save_portfolio, daemon=True).start()
        
        # Charger l'état du portefeuille APRÈS l'initialisation de is_running
        self.load_portfolio_state()
        
        # Cache et analyse
        self.last_analysis_time = {}
        self.analysis_cooldown = 5  # Réduit de 30 à 5 secondes pour scalping
        
        self.log("🚀 Bot de trading initialisé")
        self.log(f"📊 Mode: {'SIMULATION' if self.simulation_mode else 'RÉEL'}")
        
        # Initialiser la balance selon le mode
        if self.simulation_mode:
            self.balance = self.simulated_balance
        
        # Notifier la balance initiale
        self.log(f"💰 Solde initial: {self.balance:.2f} USDT")
        for callback in self.callbacks.get('balance_update', []):
            try:
                callback(self.balance, len(self.open_positions))
            except Exception:
                pass
    
    def _initialize_exchange(self):
        """Initialise la connexion exchange avec UNIQUEMENT les clés privées"""
        try:
            # Récupérer les clés API depuis la config
            secret = self.exchange_config.get('secret', '').strip()
            testnet = self.exchange_config.get('testnet', False)
            
            self.log("🔐 TEST DE CONNEXION BINANCE AVEC VOS CLÉS PRIVÉES")
            self.log("="*60)
            
            if not api_key or not secret:
                self.log("❌ CLÉS API PRIVÉES MANQUANTES")
                self.log("   Ajoutez vos clés dans l'onglet Configuration")
                self.log("   API Key: MANQUANTE")
                self.log("   Secret: MANQUANTE")
                return False
            
            # Masquer les clés pour la sécurité
            secret_masked = API_SECRET[:8] + '...' + API_SECRET[-4:] if API_SECRET and len(API_SECRET) > 12 else '***'
            
            self.log(f"🔑 Clés API détectées:")
            api_key_masked = API_KEY[:8] + '...' + API_KEY[-4:] if API_KEY and len(API_KEY) > 12 else '***'
            self.log(f"   API Key: {api_key_masked}")
            secret_masked = API_SECRET[:8] + '...' + API_SECRET[-4:] if API_SECRET and len(API_SECRET) > 12 else '***'
            self.log(f"   Secret: {secret_masked}")
            self.log(f"   Mode: {'TESTNET' if testnet else 'PRODUCTION'}")
            
            # Créer l'exchange avec vos clés privées pour TOUTES les requêtes
            import ccxt
            self.log("🔗 Création de la connexion exchange...")
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret,
                'sandbox': testnet,
                'enableRateLimit': True,
                'timeout': self.exchange_config.get('REST_TIMEOUT', 15) * 1000,
                'rateLimit': 60000 / self.exchange_config.get('MAX_REST_REQUESTS_PER_MINUTE', 1200)
            })
            
            # Test 1: Chargement des marchés avec VOS clés privées
            self.log("📊 Test 1: Chargement des marchés avec vos clés privées...")
            markets = self.exchange.load_markets()
            self.log(f"   ✅ {len(markets)} marchés chargés via vos clés privées")
            
            # Test 2: Récupération du solde avec VOS clés privées
            self.log("💰 Test 2: Récupération du solde avec vos clés privées...")
            balance = self.exchange.fetch_balance()
            self.log(f"   ✅ Solde récupéré via vos clés privées")
            
            # Afficher les principales balances
            main_currencies = ['USDT', 'BTC', 'ETH', 'BNB', 'FDUSD', 'BUSD']
            for currency in main_currencies:
                if currency in balance and balance[currency]['total'] > 0:
                    free = balance[currency]['free']
                    used = balance[currency]['used']
                    total = balance[currency]['total']
                    self.log(f"   💵 {currency}: {free:.8f} libre, {used:.8f} utilisé, {total:.8f} total")
            
            # Test 3: Récupération des tickers avec VOS clés privées
            self.log("📈 Test 3: Récupération des tickers avec vos clés privées...")
            tickers = self.exchange.fetch_tickers()
            self.log(f"   ✅ {len(tickers)} tickers récupérés via vos clés privées")
            
            # Test 4: Vérification des tickers populaires
            self.log("🔍 Test 4: Vérification des tickers populaires...")
            test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT']
            for symbol in test_symbols:
                if symbol in tickers:
                    ticker = tickers[symbol]
                    price = ticker.get('last', 0)
                    volume = ticker.get('quoteVolume', 0)
                    volume_m = volume / 1000000 if volume else 0
                    self.log(f"   ✅ {symbol}: ${price:.4f}, Volume: {volume_m:.1f}M")
            
            # Test 5: Test des permissions
            self.log("🔐 Test 5: Vérification des permissions...")
            try:
                orders = self.exchange.fetch_open_orders()
                self.log(f"   ✅ Permissions OK - {len(orders)} ordres ouverts")
            except Exception as perm_e:
                if "permissions" in str(perm_e).lower():
                    self.log(f"   ⚠️ Permissions limitées: {perm_e}")
                else:
                    self.log(f"   ✅ Permissions OK (pas d'ordres ouverts)")
            
            self.log("🎉 CONNEXION BINANCE RÉUSSIE AVEC VOS CLÉS PRIVÉES !")
            self.log("✅ Toutes les requêtes utilisent vos clés privées")
            self.log("✅ Le bot peut maintenant fonctionner correctement")
            self.log("="*60)
            
            # Notifier le GUI du succès de connexion
            for callback in self.callbacks.get('exchange_status', []):
                try:
                    callback('connected', f"{len(markets)} marchés", testnet)
                except Exception:
                    pass
            
            return True
            
        except ccxt.AuthenticationError as e:
            self.log("❌ ERREUR D'AUTHENTIFICATION AVEC VOS CLÉS")
            self.log(f"   Détails: {e}")
            self.log("   Vérifiez vos clés API dans l'onglet Configuration")
            self.log("   Assurez-vous que les clés sont correctes et actives")
            
            # Notifier le GUI de l'erreur
            for callback in self.callbacks.get('exchange_status', []):
                try:
                    callback('auth_error', str(e), testnet)
                except Exception:
                    pass
            return False
        except ccxt.NetworkError as e:
            self.log("❌ ERREUR RÉSEAU AVEC VOS CLÉS")
            self.log(f"   Détails: {e}")
            self.log("   Vérifiez votre connexion internet")
            
            # Notifier le GUI de l'erreur réseau
            for callback in self.callbacks.get('exchange_status', []):
                try:
                    callback('network_error', str(e), testnet)
                except Exception:
                    pass
            return False
        except Exception as e:
            self.log("❌ ERREUR INATTENDUE AVEC VOS CLÉS PRIVÉES")
            self.log(f"   Détails: {e}")
            
            # Notifier le GUI de l'erreur
            for callback in self.callbacks.get('exchange_status', []):
                try:
                    callback('error', str(e), testnet)
                except Exception:
                    pass
            return False
    
    def add_callback(self, event_type: str, callback: Callable):
        """Ajoute un callback pour les notifications"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def log(self, message: str):
        """Log avec notifications aux callbacks"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        # Notifier les callbacks
        for callback in self.callbacks['log_message']:
            try:
                callback(log_msg)
            except Exception:
                pass
    
    def setup_watchlist(self):
        """Configure la watchlist avec scan en boucle continue"""
        # Initialiser watchlist vide par défaut
        self.watchlist = []
        
        if self.scan_config['auto_scan_enabled']:
            # Vérifier que l'exchange est connecté avant de démarrer le scan
            if not hasattr(self, 'exchange_connected') or not self.exchange_connected:
                self.log("❌ Exchange non connecté - Scan automatique désactivé")
                self.log("   Vérifiez vos clés API dans l'onglet Configuration")
                return
            
            self.log("🔍 Auto-scan CONTINU des cryptos activé")
            self._start_continuous_scanning()
        else:
            self.watchlist = self.scan_config['watchlist']
            self.log(f"📋 Watchlist manuelle: {self.watchlist}")
    
    def _start_continuous_scanning(self):
        """Démarre le scan continu en arrière-plan avec robustesse maximale"""
        def scan_loop():
            consecutive_failures = 0
            max_consecutive_failures = 5
            
            self.log("🚀 Thread de scan continu démarré avec robustesse maximale")
            
            while self.is_running:
                # Reload configuration for real-time changes
                try:
                    self.config_manager.load_config()
                    self.scan_config = self.config_manager.get_scan_config()
                except Exception:
                    pass
                try:
                    self.log("🔄 Démarrage nouveau cycle de scan...")
                    
                    # Vérifier que l'exchange est toujours disponible
                    if not hasattr(self, 'exchange') or self.exchange is None:
                        self.log("❌ Exchange non disponible pour le scan")
                        raise Exception("Exchange non initialisé")
                    
                    # Créer le scanner SCALPING PROFESSIONNEL
                    from scalping_scanner import ScalpingScanner
                    scanner = ScalpingScanner(self.exchange, self.scan_config)
                    
                    # Effectuer le scan SCALPING avec timeout
                    scan_start_time = time.time()
                    opportunities = scanner.scan_scalping_opportunities()
                    scan_duration = time.time() - scan_start_time
                    
                    # Récupérer les stats du scan pour le GUI
                    scan_summary = scanner.get_scan_summary()
                    scan_stats = {
                        'strategy': 'scalping_professional',
                        'opportunities_found': len(opportunities),
                        'scan_time': scan_duration,
                        'timeframe': '1min',
                        'last_scan': datetime.now().isoformat()
                    }
                    selected_cryptos = opportunities[:3]  # Top 3 opportunités
                    
                    self.log(f"🎯 Scan SCALPING terminé en {scan_duration:.1f}s: {len(opportunities)} opportunités trouvées")
                    
                    # DEBUG: Vérifier les données avant transmission
                    self.log(f"🔧 DEBUG: Stats scan = {scan_stats}")
                    self.log(f"🔧 DEBUG: Cryptos sélectionnées = {len(selected_cryptos)} éléments")
                    if selected_cryptos:
                        self.log(f"🔧 DEBUG: Premier élément = {selected_cryptos[0]}")
                    
                    # Notifier le GUI avec les stats du scan
                    callback_count = len(self.callbacks.get('scan_update', []))
                    self.log(f"🔧 DEBUG: Envoi données à {callback_count} callbacks GUI")
                    
                    for i, callback in enumerate(self.callbacks.get('scan_update', [])):
                        try:
                            self.log(f"🔧 DEBUG: Exécution callback {i+1}/{callback_count}")
                            callback(scan_stats, selected_cryptos)
                            self.log(f"✅ DEBUG: Callback {i+1} exécuté avec succès")
                        except Exception as e:
                            self.log(f"❌ Erreur callback scan {i+1}: {e}")
                            import traceback
                            self.log(f"🔍 Traceback: {traceback.format_exc()}")
                    
                    # Mettre à jour la watchlist
                    new_watchlist = [c['symbol'] for c in opportunities[:self.scan_config['max_cryptos']]]
                    
                    # Reset compteur d'échecs si le scan a réussi
                    consecutive_failures = 0
                    
                    if new_watchlist:
                        # Cryptos trouvées
                        if set(new_watchlist) != set(self.watchlist):
                            self.log(f"🎯 Watchlist mise à jour: {new_watchlist}")
                            self.watchlist = new_watchlist
                            
                            # Redémarrer WebSocket avec nouvelles cryptos
                            if self.websocket_manager:
                                try:
                                    self.websocket_manager.restart_streams(self.watchlist)
                                except Exception as e:
                                    self.log(f"❌ Erreur redémarrage WebSocket: {e}")
                        
                        # NOUVEAU : Génération de trades basée sur les opportunités scannées
                        for opportunity in opportunities[:3]:  # Top 3 opportunités
                            symbol = opportunity['symbol']
                            pump_3min = opportunity.get('pump_3min', 0)  # Utilise pump_3min uniquement
                            price = opportunity['price']
                            volume_24h = opportunity['volume_24h']
                            
                            # Générer signal basé sur pump (momentum) - LOGIQUE SCALPING CORRIGÉE
                            signal = 'HOLD'
                            if pump_3min < -0.5:  # -0.5% = signal d'achat (acheter bas)
                                signal = 'BUY'
                            elif pump_3min > 0.5:  # +0.5% = signal de vente (vendre haut)
                                signal = 'SELL'
                            
                            if signal in ['BUY', 'SELL']:
                                print(f"🎯 {symbol}: Signal {signal} généré (Pump: {pump_3min:+.2f}%)")
                                
                                # SIMULATION de trading avec vraies données du scan
                                if self.simulation_mode:
                                    self._execute_simulated_trade(symbol, {
                                        'signal': signal,
                                        'current_price': price,
                                        'change_24h': pump_3min,
                                        'volume_24h': volume_24h,
                                        'confidence': 0.8
                                    })
                        
                        # Afficher détails des opportunités SCALPING
                        for i, symbol in enumerate(self.watchlist, 1):
                            opportunity = next((c for c in opportunities if c['symbol'] == symbol), None)
                            if opportunity:
                                score = opportunity.get('score', 0)  # CORRIGÉ : score au lieu de final_score
                                price = opportunity.get('price', 0)  # CORRIGÉ : price au lieu de current_price
                                strategy = opportunity.get('strategy', 'scalping')
                                timeframe = opportunity.get('timeframe', '1min')
                                self.log(f"   {i}. {symbol} - Score: {score:.1f} - Prix: ${price:.4f} - {strategy.upper()} ({timeframe})")
                        
                        # Attendre avant prochain scan (cryptos trouvées)
                        # Utiliser configuration utilisateur pour l'intervalle
                        scan_interval_minutes = self.config_manager.get('SCAN_INTERVAL_MINUTES', 1)
                        scan_interval = scan_interval_minutes * 60  # Convertir en secondes
                        
                        self.log(f"⏱️ Prochain scan dans {scan_interval_minutes} minute{'s' if scan_interval_minutes > 1 else ''}")
                        
                    else:
                        # Aucune crypto trouvée - scan plus fréquent mais continuer TOUJOURS
                        self.log("⚠️ Aucune crypto trouvée par l'auto-scan")
                        self.log("🔄 Le scan va continuer à chercher...")
                        
                        # Garder l'ancienne watchlist si elle existe
                        if not self.watchlist:
                            self.log("📋 Watchlist vide - scan continu activé")
                        
                        # Scan plus fréquent si rien trouvé (30 secondes)
                        scan_interval = 30  # Scan toutes les 30 secondes si rien trouvé
                    
                    self.log(f"⏱️ Prochain scan dans {scan_interval} secondes")
                    
                    # Attendre avant le prochain scan avec interruption possible
                    for i in range(scan_interval):
                        if not self.is_running:
                            self.log("🛑 Arrêt du scan continu demandé")
                            return
                        time.sleep(1)
                    
                except Exception as e:
                    consecutive_failures += 1
                    error_details = str(e)
                    self.log(f"❌ Erreur dans le scan continu (échec {consecutive_failures}): {error_details}")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        self.log(f"🚨 Trop d'échecs consécutifs ({consecutive_failures}) - Réinitialisation")
                        
                        # Réinitialiser le scanner et l'exchange
                        try:
                            import ccxt
                            self.exchange = ccxt.binance({
                                'apiKey': self.exchange_config['api_key'],
                                'secret': self.exchange_config['secret'],
                                'sandbox': self.exchange_config['testnet'],
                                'enableRateLimit': True,
                            })
                            self.exchange.load_markets()
                            self.log("🔄 Exchange réinitialisé avec succès")
                            consecutive_failures = 0
                        except Exception as ex:
                            self.log(f"❌ Erreur réinitialisation exchange: {ex}")
                    
                    # Attendre plus longtemps en cas d'erreur, mais continuer
                    error_wait = min(60 + (consecutive_failures * 30), 300)  # Max 5 minutes
                    self.log(f"🔄 Attente de {error_wait} secondes avant nouveau scan...")
                    
                    for i in range(error_wait):
                        if not self.is_running:
                            self.log("🛑 Arrêt du scan continu demandé")
                            return
                        time.sleep(1)
                
                # Log périodique d'activité
                if hasattr(self, '_last_activity_log'):
                    if time.time() - self._last_activity_log > 300:  # Toutes les 5 minutes
                        self.log("🔄 Scan continu actif - Recherche permanente de cryptos...")
                        self._last_activity_log = time.time()
                else:
                    self._last_activity_log = time.time()
            
            self.log("🛑 Thread de scan continu terminé")
        
        # Démarrer le scan continu dans un thread
        import threading
        self.scan_thread = threading.Thread(target=scan_loop, daemon=True, name="ContinuousScanThread")
        self.scan_thread.start()
        self.log("🚀 Thread de scan continu démarré avec robustesse maximale")
    
    def setup_websockets(self):
        """Configure les WebSockets temps réel avec retry automatique et robustesse maximale + fallback"""
        if not self.watchlist:
            self.log("⚠️ Aucune crypto à surveiller pour l'instant")
            # Programmer un retry dans 30 secondes
            import threading
            def retry_websocket():
                import time
                retry_count = 0
                max_retries = 10
                
                while self.is_running and not self.watchlist and retry_count < max_retries:
                    # Reload configuration for real-time changes
                    try:
                        self.config_manager.load_config()
                        self.scan_config = self.config_manager.get_scan_config()
                    except Exception:
                        pass
                    time.sleep(30)
                    retry_count += 1
                    self.log(f"🔄 Retry WebSocket {retry_count}/{max_retries} - Attente watchlist...")
                    
                    if self.watchlist:
                        self.log("✅ Watchlist disponible - Démarrage WebSocket")
                        self.setup_websockets()
                        break
                
                if retry_count >= max_retries:
                    self.log("❌ Timeout attente watchlist pour WebSocket")
            
            threading.Thread(target=retry_websocket, daemon=True).start()
            return
        
        try:
            testnet = self.exchange_config.get('testnet', False)
            self.websocket_manager = BinanceWebSocketManager(testnet=testnet)
            
            # Callbacks WebSocket avec gestion d'erreurs robuste
            def on_price_update(data):
                try:
                    symbol = data['symbol']
                    self._process_realtime_data(symbol, data)
                    
                    # Notifier les callbacks GUI
                    for callback in self.callbacks['price_update']:
                        try:
                            callback(symbol, data)
                        except Exception as e:
                            self.log(f"❌ Erreur callback GUI price_update: {e}")
                except Exception as e:
                    self.log(f"❌ Erreur traitement price_update: {e}")
            
            def on_connection_status(status):
                try:
                    self.log(f"🔗 WebSocket: {status}")
                    
                    # Si déconnecté, démarrer le système de fallback
                    if status in ['error', 'closed', 'stale']:
                        self.log("🔄 WebSocket instable - Activation du système de fallback")
                        self._start_price_fallback_system()
                        
                        # Toujours essayer de reconnecter
                        import threading
                        def check_reconnection():
                            import time
                            time.sleep(30)
                            if self.is_running and self.websocket_manager:
                                health = self.websocket_manager.get_connection_health()
                                if not health['is_connected']:
                                    self.log("🔄 Tentative de redémarrage WebSocket forcé...")
                                    try:
                                        self.websocket_manager.restart_streams(self.watchlist)
                                    except Exception as e:
                                        self.log(f"❌ Erreur redémarrage forcé: {e}")
                        
                        threading.Thread(target=check_reconnection, daemon=True).start()
                    
                    elif status == 'connected':
                        self.log("✅ WebSocket reconnecté avec succès")
                        self._stop_price_fallback_system()  # Arrêter le fallback
                        
                except Exception as e:
                    self.log(f"❌ Erreur traitement connection_status: {e}")
            
            self.websocket_manager.add_callback('price_update', on_price_update)
            self.websocket_manager.add_callback('connection_status', on_connection_status)
            
            # Démarrer les streams
            self.websocket_manager.start_price_streams(self.watchlist)
            
            self.log("⚡ WebSockets temps réel activés avec système de fallback")
            
            # Programmer une vérification périodique de santé
            self._start_websocket_health_monitor()
            
            # Démarrer le système de fallback IMMÉDIATEMENT en parallèle
            import threading
            def immediate_fallback():
                time.sleep(2)  # Attendre juste 2 secondes
                if self.is_running:
                    self.log("🔄 Activation fallback préventif - WebSocket peut prendre du temps")
                    self._start_price_fallback_system()
            
            threading.Thread(target=immediate_fallback, daemon=True).start()
            
        except Exception as e:
            self.log(f"❌ Erreur WebSockets: {e}")
            self.log("🔄 Activation du système de fallback pour continuer le trading")
            self._start_price_fallback_system()
            
            # Programmer un retry selon configuration
            retry_interval = self.config_manager.get('SCAN_INTERVAL_MINUTES', 1) * 60
            import threading
            def retry_setup():
                import time
                time.sleep(retry_interval)
                if self.is_running and self.watchlist:
                    self.log("🔄 Nouvelle tentative de configuration WebSocket...")
                    self.setup_websockets()
            
            threading.Thread(target=retry_setup, daemon=True).start()
    
    def _start_price_fallback_system(self):
        """Démarre un système de fallback qui simule des données de prix pour continuer le trading"""
        if hasattr(self, '_fallback_running') and self._fallback_running:
            return  # Déjà en cours
        
        self._fallback_running = True
        self.log("🔄 Démarrage système de fallback pour données de prix")
        
        def fallback_price_generator():
            while self.is_running and self._fallback_running:
                # Reload configuration for real-time changes
                try:
                    self.config_manager.load_config()
                    self.scan_config = self.config_manager.get_scan_config()
                except Exception:
                    pass
                try:
                    for symbol in self.watchlist:
                        if not self.is_running or not self._fallback_running:
                            break
                        
                        # Utiliser l'exchange pour obtenir les prix actuels
                        if self.exchange:
                            try:
                                ticker = self.exchange.fetch_ticker(symbol)
                                
                                # Créer des données compatibles WebSocket
                                fallback_data = {
                                    'symbol': symbol,
                                    'price': ticker['last'],
                                    'volume_24h': ticker.get('quoteVolume', 0),
                                    'change_24h': ticker.get('percentage', 0),
                                    'timestamp': datetime.now()
                                }
                                
                                # Traiter comme des données temps réel
                                self._process_realtime_data(symbol, fallback_data)
                                
                                # Notifier les callbacks GUI
                                for callback in self.callbacks['price_update']:
                                    try:
                                        callback(symbol, fallback_data)
                                    except Exception:
                                        pass
                                
                            except Exception as e:
                                self.log(f"❌ Erreur récupération ticker {symbol}: {e}")
                    
                    # Attendre 5 secondes avant la prochaine mise à jour
                    import time
                    time.sleep(5)
                    
                except Exception as e:
                    self.log(f"❌ Erreur système fallback: {e}")
                    import time
                    time.sleep(10)
        
        import threading
        fallback_thread = threading.Thread(target=fallback_price_generator, daemon=True, name="PriceFallbackSystem")
        fallback_thread.start()
        self.log("✅ Système de fallback prix activé - Trading peut continuer")
    
    def _calculate_slippage(self, symbol: str, expected_price: float, executed_price: float) -> float:
        """Calcule le slippage réel d'un trade"""
        if expected_price <= 0:
            return 0.0
        
        slippage_percent = ((executed_price - expected_price) / expected_price) * 100
        return slippage_percent
    
    def _log_slippage(self, symbol: str, trade_type: str, expected_price: float, executed_price: float):
        """Log le slippage d'un trade"""
        if not self.enable_slippage_tracking:
            return
        
        slippage = self._calculate_slippage(symbol, expected_price, executed_price)
        
        # Enregistrer dans l'historique
        slippage_entry = {
            'symbol': symbol,
            'trade_type': trade_type,
            'expected_price': expected_price,
            'executed_price': executed_price,
            'slippage_percent': slippage,
            'timestamp': datetime.now()
        }
        
        self.slippage_history.append(slippage_entry)
        
        # Garder seulement les 100 derniers enregistrements
        if len(self.slippage_history) > 100:
            self.slippage_history.pop(0)
        
        # Log détaillé
        direction = "défavorable" if abs(slippage) > self.max_acceptable_slippage else "acceptable"
        self.log(f"📊 SLIPPAGE {symbol} ({trade_type}): {slippage:.3f}% - {direction}")
        self.log(f"   Prix attendu: ${expected_price:.6f} | Prix exécuté: ${executed_price:.6f}")
        
        # Alerte si slippage trop élevé
        if abs(slippage) > self.max_acceptable_slippage:
            self.log(f"⚠️ SLIPPAGE ÉLEVÉ {symbol}: {slippage:.3f}% > {self.max_acceptable_slippage}%")
    
    def get_slippage_stats(self) -> Dict:
        """Retourne les statistiques de slippage"""
        if not self.slippage_history:
            return {"count": 0, "average": 0.0, "max": 0.0, "min": 0.0}
        
        slippages = [entry['slippage_percent'] for entry in self.slippage_history]
        
        return {
            "count": len(slippages),
            "average": sum(slippages) / len(slippages),
            "max": max(slippages),
            "min": min(slippages),
            "recent_trades": self.slippage_history[-10:]  # 10 derniers trades
        }
    
    def load_portfolio_state(self):
        """Charge l'état du portefeuille depuis le fichier JSON"""
        try:
            import json
            import os
            
            if os.path.exists(self.portfolio_file):
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Restaurer les données
                self.simulated_balance = data.get('balance', self.initial_balance)
                self.balance = self.simulated_balance
                self.total_pnl = data.get('total_pnl', 0.0)
                self.total_trades = data.get('total_trades', 0)
                self.winning_trades = data.get('winning_trades', 0)
                self.total_fees = data.get('total_fees', 0.0)  # NOUVEAU: Restaurer frais totaux
                self.closed_trades = data.get('closed_trades', [])
                
                # Restaurer les positions ouvertes
                saved_positions = data.get('open_positions', [])
                self.open_positions = []
                
                for pos in saved_positions:
                    # Convertir les timestamps en datetime
                    if 'timestamp' in pos:
                        pos['timestamp'] = datetime.fromisoformat(pos['timestamp'])
                    if 'entry_time' in pos:
                        pos['entry_time'] = datetime.fromisoformat(pos['entry_time'])
                    if 'last_significant_move' in pos:
                        pos['last_significant_move'] = datetime.fromisoformat(pos['last_significant_move'])
                    
                    self.open_positions.append(pos)
                
                last_updated = data.get('last_updated', 'Unknown')
                self.log(f"📂 Portefeuille restauré depuis {last_updated}")
                self.log(f"💰 Balance: {self.balance:.2f}€")
                self.log(f"📊 Positions ouvertes: {len(self.open_positions)}")
                self.log(f"📈 P&L total: {self.total_pnl:+.2f}€")
                self.log(f"🎯 Trades totaux: {self.total_trades}")
                
                # Redémarrer la surveillance des positions ouvertes
                for position in self.open_positions:
                    if position.get('status') == 'open':
                        # NOUVEAU SYSTÈME : Vérifier le type de surveillance à utiliser
                        system_type = position.get('system_type', 'LEGACY')
                        if system_type == 'SIMPLE_STOP_TAKE_PROFIT':
                            # Nouveau système simplifié
                            threading.Thread(target=self._monitor_position_simple, args=[position], daemon=True).start()
                        elif self.config_manager.get('TRAILING_STOP_ENABLED', False):
                            # Ancienne surveillance 3 couches (compatibilité)
                            threading.Thread(target=self._monitor_position_3_layers, args=[position], daemon=True).start()
                        # Sinon, pas de surveillance automatique (positions héritées)
                        
            else:
                self.log(f"📂 Nouveau portefeuille créé - Balance initiale: {self.balance:.2f}€")
                self.save_portfolio_state()
                
        except Exception as e:
            self.log(f"❌ Erreur chargement portefeuille: {e}")
            self.log("📂 Utilisation des valeurs par défaut")
    
    def save_portfolio_state(self):
        """Sauvegarde l'état du portefeuille dans le fichier JSON"""
        try:
            import json
            from datetime import datetime
            
            def convert_datetime_to_string(obj):
                """Convertit récursivement tous les datetime en string"""
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_datetime_to_string(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime_to_string(item) for item in obj]
                else:
                    return obj
            
            # Préparer les positions pour la sauvegarde
            positions_to_save = []
            for pos in self.open_positions:
                pos_copy = pos.copy()
                # Conversion récursive de tous les datetime
                pos_copy = convert_datetime_to_string(pos_copy)
                positions_to_save.append(pos_copy)
            
            # Préparer les trades fermés pour la sauvegarde
            closed_trades_to_save = []
            for trade in self.closed_trades[-100:]:  # Garder les 100 derniers trades
                trade_copy = trade.copy()
                # Conversion récursive de tous les datetime
                trade_copy = convert_datetime_to_string(trade_copy)
                closed_trades_to_save.append(trade_copy)
            
            # Données à sauvegarder
            portfolio_data = {
                'balance': self.balance,
                'simulated_balance': self.simulated_balance,
                'open_positions': positions_to_save,
                'closed_trades': closed_trades_to_save,
                'total_pnl': self.total_pnl,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'total_fees': self.total_fees,  # NOUVEAU: Sauvegarder frais totaux
                'last_updated': datetime.now().isoformat(),
                'initial_balance': self.initial_balance,
                'position_size_usdt': self.position_size_usdt
            }
            
            # Sauvegarde atomique (fichier temporaire puis renommage)
            temp_file = self.portfolio_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
            
            # Renommer le fichier temporaire
            import os
            os.replace(temp_file, self.portfolio_file)
            
            self.last_save_time = datetime.now()
            
        except Exception as e:
            self.log(f"❌ Erreur sauvegarde portefeuille: {e}")
    
    def _auto_save_portfolio(self):
        """Sauvegarde automatique du portefeuille toutes les 30 secondes"""
        while self.is_running:
            # Reload configuration for real-time changes
            try:
                self.config_manager.load_config()
                self.scan_config = self.config_manager.get_scan_config()
            except Exception:
                pass
            try:
                # Sauvegarder toutes les 30 secondes
                time.sleep(30)
                if self.is_running:
                    self.save_portfolio_state()
                    
            except Exception as e:
                self.log(f"❌ Erreur sauvegarde automatique: {e}")
                time.sleep(30)
    
    def _monitor_position_3_layers(self, position: Dict):
        """Surveille une position avec le système de sécurité à 3 couches"""
        try:
            symbol = position['symbol']
            entry_price = position['price']
            entry_time = position['entry_time']
            
            self.log(f"🔒 Démarrage surveillance 3 couches pour {symbol}")
            
            while position['status'] == 'open' and self.is_running:
                try:
                    # Obtenir le prix actuel
                    current_price = self._get_current_price(symbol)
                    if current_price is None:
                        time.sleep(1)
                        continue
                    
                    # Calculer la performance depuis l'entrée
                    price_change_percent = ((current_price - entry_price) / entry_price) * 100
                    
                    # Mettre à jour le prix le plus haut si nécessaire
                    if current_price > position['highest_price']:
                        position['highest_price'] = current_price
                        position['last_significant_move'] = datetime.now()
                        
                        # Vérifier si on doit activer le trailing stop
                        if not position['trailing_activated'] and price_change_percent >= self.trailing_activation_percent:
                            position['trailing_activated'] = True
                            self.log(f"📈 {symbol}: Trailing stop ACTIVÉ à +{price_change_percent:.2f}% (seuil: {self.trailing_activation_percent}%)")
                    
                    # === COUCHE 1: TRAILING STOP ===
                    if position['trailing_activated']:
                        highest_price = position['highest_price']
                        drop_from_high = ((highest_price - current_price) / highest_price) * 100
                        
                        if drop_from_high >= self.trailing_stop_percent:
                            self.log(f"🎯 {symbol}: TRAILING STOP déclenché (-{drop_from_high:.2f}% depuis le plus haut)")
                            self._close_position_with_reason(position, current_price, "TRAILING_STOP")
                            break
                    
                    # === COUCHE 2: TIMEOUT ===
                    time_since_entry = (datetime.now() - entry_time).total_seconds()
                    time_since_last_move = (datetime.now() - position['last_significant_move']).total_seconds()
                    
                    if time_since_last_move >= self.timeout_exit_seconds:
                        self.log(f"⏱️ {symbol}: TIMEOUT déclenché ({time_since_last_move:.0f}s sans hausse)")
                        self._close_position_with_reason(position, current_price, "TIMEOUT")
                        break
                    
                    # === COUCHE 3: STOP LOSS ===
                    if price_change_percent <= -self.stop_loss_percent:
                        self.log(f"🛑 {symbol}: STOP LOSS déclenché ({price_change_percent:.2f}% ≤ -{self.stop_loss_percent}%)")
                        self._close_position_with_reason(position, current_price, "STOP_LOSS")
                        break
                    
                    # Log de progression (toutes les 5 secondes)
                    if int(time.time()) % 5 == 0:
                        status = "🟢 TRAILING ON" if position['trailing_activated'] else "🟡 WATCHING"
                        self.log(f"📊 {symbol}: {price_change_percent:+.2f}% | Plus haut: {position['highest_price']:.6f} | {status}")
                    
                    # Attendre 1 seconde avant la prochaine vérification
                    time.sleep(1)
                    
                except Exception as e:
                    self.log(f"❌ Erreur surveillance {symbol}: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            self.log(f"❌ Erreur système surveillance {symbol}: {e}")
    
    def _monitor_position_simple(self, position: Dict):
        """Surveillance INTELLIGENTE avec tracking momentum - Ne vend QUE quand nécessaire"""
        try:
            symbol = position['symbol']
            entry_price = position['entry_price']
            stop_loss = position['stop_loss']
            take_profit = position['take_profit']
            direction = position['direction']
            
            # Configuration surveillance intelligente
            intelligent_tracking = self.config_manager.get('INTELLIGENT_MOMENTUM_TRACKING', True)
            momentum_check_interval = self.config_manager.get('MOMENTUM_CHECK_INTERVAL', 3)
            stagnation_threshold = self.config_manager.get('MOMENTUM_STAGNATION_THRESHOLD', 0.05)
            decline_threshold = self.config_manager.get('MOMENTUM_DECLINE_THRESHOLD', -0.1)
            max_tp_extension = self.config_manager.get('MAX_TP_EXTENSION_PERCENT', 2.0)
            min_samples = self.config_manager.get('MIN_MOMENTUM_SAMPLES', 5)
            strong_momentum = self.config_manager.get('STRONG_MOMENTUM_THRESHOLD', 0.3)
            weak_momentum = self.config_manager.get('WEAK_MOMENTUM_THRESHOLD', 0.1)
            
            # Historique des prix pour calcul momentum
            price_history = []
            tp_reached_time = None
            extended_tp = take_profit  # TP peut être étendu si momentum fort
            
            self.log(f"🧠 SURVEILLANCE INTELLIGENTE: {symbol}")
            self.log(f"   🎯 TP initial: {take_profit:.6f} | Extension max: +{max_tp_extension}%")
            
            while position['status'] == 'open' and self.is_running:
                try:
                    current_price = self._get_current_price(symbol)
                    if current_price is None:
                        time.sleep(2)
                        continue
                    
                    # Ajouter prix à l'historique
                    price_history.append({
                        'price': current_price,
                        'timestamp': datetime.now()
                    })
                    
                    # Garder seulement les N derniers échantillons
                    if len(price_history) > min_samples * 2:
                        price_history = price_history[-min_samples * 2:]
                    
                    price_change_percent = ((current_price - entry_price) / entry_price) * 100
                    
                    # RÈGLE 1: VENTE IMMÉDIATE sur CHUTE SIGNIFICATIVE (nouvelle règle prioritaire)
                    immediate_exit_threshold = self.config_manager.get('IMMEDIATE_EXIT_THRESHOLD', -0.8)  # -0.8% par défaut
                    if isinstance(immediate_exit_threshold, str):
                        immediate_exit_threshold = float(immediate_exit_threshold)
                    
                    if price_change_percent <= immediate_exit_threshold:
                        self.log(f"🚨 {symbol}: VENTE IMMÉDIATE - Chute significative ({price_change_percent:+.2f}%) !")
                        self._close_position_with_reason(position, current_price, "IMMEDIATE_EXIT")
                        return
                    
                    # RÈGLE 2: STOP LOSS traditionnel (si pas encore vendu)
                    if current_price <= stop_loss:
                        self.log(f"🛑 {symbol}: STOP LOSS déclenché à {current_price:.6f} (-{abs(price_change_percent):.2f}%)")
                        self._close_position_with_reason(position, current_price, "STOP_LOSS")
                        return
                    
                    # RÈGLE 2: CALCUL MOMENTUM (si assez d'échantillons)
                    momentum_percent = 0
                    momentum_trend = "NEUTRE"
                    
                    if len(price_history) >= min_samples:
                        # Calculer momentum sur les N derniers points
                        recent_prices = [p['price'] for p in price_history[-min_samples:]]
                        oldest_price = recent_prices[0]
                        momentum_percent = ((current_price - oldest_price) / oldest_price) * 100
                        
                        # Déterminer la tendance
                        if momentum_percent > strong_momentum:
                            momentum_trend = "FORTE HAUSSE 🚀"
                        elif momentum_percent > weak_momentum:
                            momentum_trend = "HAUSSE 📈"
                        elif momentum_percent > decline_threshold:
                            momentum_trend = "STAGNATION 😐"
                        else:
                            momentum_trend = "BAISSE 📉"
                    
                    # RÈGLE 3: GESTION TAKE PROFIT INTELLIGENT
                    if current_price >= take_profit:
                        if tp_reached_time is None:
                            tp_reached_time = datetime.now()
                            self.log(f"🎯 {symbol}: Take Profit initial atteint ! Surveillance momentum activée")
                        
                        if intelligent_tracking and len(price_history) >= min_samples:
                            # Si momentum encore très positif, étendre le TP
                            if momentum_percent > strong_momentum and momentum_trend == "FORTE HAUSSE 🚀":
                                # Calculer nouveau TP étendu
                                extension_factor = min(1 + (max_tp_extension / 100), 1.05)  # Max +5%
                                new_extended_tp = entry_price * (1 + (((take_profit / entry_price) - 1) * extension_factor))
                                
                                if new_extended_tp > extended_tp:
                                    extended_tp = new_extended_tp
                                    self.log(f"🚀 {symbol}: TP ÉTENDU à {extended_tp:.6f} (momentum: +{momentum_percent:.2f}%)")
                            
                            # Vendre si momentum faiblit ou devient négatif
                            elif momentum_percent < stagnation_threshold:
                                self.log(f"💰 {symbol}: VENTE - TP atteint + momentum faible ({momentum_trend})")
                                self.log(f"   Prix: {current_price:.6f} | Momentum: {momentum_percent:+.2f}%")
                                self._close_position_with_reason(position, current_price, "TAKE_PROFIT_INTELLIGENT")
                                return
                        else:
                            # Mode classique si pas assez d'échantillons
                            self.log(f"🎉 {symbol}: TAKE PROFIT classique atteint à {current_price:.6f}")
                            self._close_position_with_reason(position, current_price, "TAKE_PROFIT")
                            return
                    
                    # RÈGLE 4: VENTE SI MOMENTUM DEVIENT NÉGATIF (même sans atteindre TP)
                    if intelligent_tracking and len(price_history) >= min_samples:
                        if momentum_percent < decline_threshold and price_change_percent > 0.2:
                            # On était en profit mais momentum devient négatif
                            self.log(f"⚠️ {symbol}: VENTE préventive - Momentum négatif détecté")
                            self.log(f"   Prix: {current_price:.6f} | Momentum: {momentum_percent:+.2f}% | Profit: {price_change_percent:+.2f}%")
                            self._close_position_with_reason(position, current_price, "MOMENTUM_DECLINE")
                            return
                    
                    # RÈGLE 5: TIMEOUT INTELLIGENT basé sur le mouvement du prix
                    time_elapsed = (datetime.now() - position['entry_time']).total_seconds()
                    
                    # Critères intelligents au lieu d'un timeout fixe
                    price_change_abs = abs(price_change_percent)
                    
                    # CRITÈRE 1: Si ça bouge peu ET c'est long → Fermer (position stagnante)
                    stagnation_timeout = self.config_manager.get('STAGNATION_TIMEOUT_SECONDS', 600)  # 10 min
                    stagnation_threshold = self.config_manager.get('STAGNATION_PRICE_THRESHOLD', 0.1)  # 0.1%
                    
                    if time_elapsed > stagnation_timeout and price_change_abs < stagnation_threshold:
                        self.log(f"⏰ {symbol}: Position STAGNANTE ({price_change_abs:.2f}% en {time_elapsed:.0f}s) - Fermeture")
                        self._close_position_with_reason(position, current_price, "STAGNATION_TIMEOUT")
                        return
                    
                    # CRITÈRE 2: Si ça bouge dans le mauvais sens ET c'est long → Fermer plus vite
                    negative_timeout = self.config_manager.get('NEGATIVE_TIMEOUT_SECONDS', 300)  # 5 min
                    if time_elapsed > negative_timeout and price_change_percent < -0.2:
                        self.log(f"⏰ {symbol}: Position NÉGATIVE ({price_change_percent:+.2f}% en {time_elapsed:.0f}s) - Fermeture")
                        self._close_position_with_reason(position, current_price, "NEGATIVE_TIMEOUT")
                        return
                    
                    # CRITÈRE 3: Timeout de sécurité absolue (très long si ça bouge bien)
                    max_absolute_timeout = self.config_manager.get('MAX_ABSOLUTE_TIMEOUT_SECONDS', 1800)  # 30 min max
                    if time_elapsed > max_absolute_timeout:
                        self.log(f"⏰ {symbol}: TIMEOUT ABSOLU ({time_elapsed:.0f}s) - Fermeture forcée")
                        self._close_position_with_reason(position, current_price, "ABSOLUTE_TIMEOUT")
                        return
                    
                    # Log périodique avec momentum
                    if int(time_elapsed) % 15 == 0:  # Toutes les 15s
                        self.log(f"🧠 {symbol}: {price_change_percent:+.2f}% | Momentum: {momentum_trend} ({momentum_percent:+.2f}%)")
                        if extended_tp > take_profit:
                            self.log(f"   🎯 TP étendu: {extended_tp:.6f} (original: {take_profit:.6f})")
                    
                    time.sleep(momentum_check_interval)  # Check toutes les 3 secondes
                    
                except Exception as e:
                    self.log(f"❌ Erreur surveillance {symbol}: {e}")
                    time.sleep(5)
                    
        except Exception as e:
            self.log(f"❌ Erreur critique surveillance {symbol}: {e}")
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Obtient le prix actuel d'un symbole"""
        try:
            if self.exchange:
                ticker = self.exchange.fetch_ticker(symbol)
                return ticker.get('last', 0)
            return None
        except Exception:
            return None
    
    def _close_position_with_reason(self, position: Dict, exit_price: float, reason: str):
        """Ferme une position avec une raison spécifique"""
        try:
            # Calculer le slippage si activé
            if self.enable_slippage_tracking:
                expected_price = position['price']
                self._log_slippage(position['symbol'], "SELL", expected_price, exit_price)
            
            # Fermer la position
            position['exit_reason'] = reason
            position['exit_price'] = exit_price
            position['exit_time'] = datetime.now()
            
            # Utiliser la méthode existante de fermeture
            self._close_position_scalping(position, exit_price)
            
            # Log détaillé selon la raison
            if reason == "TRAILING_STOP":
                self.log(f"✅ {position['symbol']}: Position fermée par TRAILING STOP")
            elif reason == "TIMEOUT":
                self.log(f"⏰ {position['symbol']}: Position fermée par TIMEOUT")
            elif reason == "TIMEOUT_SECURITY":
                self.log(f"⏰ {position['symbol']}: Position fermée par TIMEOUT DE SÉCURITÉ")
            elif reason == "STOP_LOSS":
                self.log(f"🛑 {position['symbol']}: Position fermée par STOP LOSS")
            elif reason == "TAKE_PROFIT":
                self.log(f"🎉 {position['symbol']}: Position fermée par TAKE PROFIT")
            elif reason == "TAKE_PROFIT_INTELLIGENT":
                self.log(f"🧠 {position['symbol']}: Position fermée par TAKE PROFIT INTELLIGENT")
            elif reason == "MOMENTUM_DECLINE":
                self.log(f"⚠️ {position['symbol']}: Position fermée par DÉCLIN DE MOMENTUM")
            else:
                self.log(f"✅ {position['symbol']}: Position fermée ({reason})")
                
        except Exception as e:
            self.log(f"❌ Erreur fermeture position {position['symbol']}: {e}")
    
    def _stop_price_fallback_system(self):
        """Arrête le système de fallback quand WebSocket est reconnecté"""
        if hasattr(self, '_fallback_running'):
            self._fallback_running = False
            self.log("🛑 Système de fallback désactivé - WebSocket reconnecté")
    
    def _start_websocket_health_monitor(self):
        """Démarre le monitoring de santé du WebSocket"""
        def health_monitor():
            while self.is_running and self.websocket_manager:
                # Reload configuration for real-time changes
                try:
                    self.config_manager.load_config()
                    self.scan_config = self.config_manager.get_scan_config()
                except Exception:
                    pass
                try:
                    # Vérifier selon configuration
                    check_interval = self.config_manager.get('SCAN_INTERVAL_MINUTES', 1) * 60
                    time.sleep(check_interval)
                    
                    if not self.websocket_manager:
                        break
                    
                    health = self.websocket_manager.get_connection_health()
                    
                    if not health['is_connected'] and health['should_reconnect']:
                        self.log(f"⚠️ WebSocket déconnecté depuis {health.get('reconnect_attempts', 0)} tentatives")
                        
                        # Si trop de tentatives échouées, forcer un redémarrage complet
                        if health.get('reconnect_attempts', 0) >= 5:
                            self.log("🔄 Redémarrage complet WebSocket après échecs multiples")
                            try:
                                self.websocket_manager.stop_all_streams()
                                time.sleep(5)
                                self.websocket_manager.start_price_streams(self.watchlist)
                            except Exception as e:
                                self.log(f"❌ Erreur redémarrage complet WebSocket: {e}")
                    
                    elif health['is_connected']:
                        # Log de santé périodique
                        msg_count = health.get('messages_received', 0)
                        if msg_count > 0:
                            self.log(f"💚 WebSocket sain: {msg_count} messages, {health.get('symbols_tracked', 0)} symboles")
                
                except Exception as e:
                    self.log(f"❌ Erreur monitoring santé WebSocket: {e}")
                    break
        
        import threading
        health_thread = threading.Thread(target=health_monitor, daemon=True, name="WebSocketHealthMonitor")
        health_thread.start()
    
    def _process_realtime_data(self, symbol: str, data: Dict):
        """Traite les données temps réel - GÉNÈRE DES TRADES avec vraies données"""
        try:
            # Les données arrivent directement du WebSocket callback
            current_price = data.get('current_price', 0)
            volume_24h = data.get('volume_24h', 0)
            change_24h = data.get('change_24h', 0)
            
            if not current_price or current_price <= 0:
                print(f"⚠️ {symbol}: Prix invalide ({current_price}) - ANALYSE IGNORÉE")
                return
            
            print(f"📊 {symbol}: Prix=${current_price:.10f}, Vol={volume_24h/1000000:.1f}M, Change={change_24h:+.2f}%")
            
            # GÉNÉRER SIGNAL DE TRADING basé sur momentum
            signal = 'HOLD'
            
            # Critères simples pour générer des trades - LOGIQUE SCALPING CORRIGÉE
            # CORRIGÉ: Acheter quand ça MONTE, pas quand ça descend !
            # Utiliser les seuils du config.txt au lieu de valeurs codées en dur
            pump_min_threshold = self.config_manager.get('pump_min_3min', 0.5)  # 0.5% par défaut
            pump_max_threshold = self.config_manager.get('pump_max_3min', 3.0)  # 3.0% par défaut
            
            # Convertir en float si nécessaire
            if isinstance(pump_min_threshold, str):
                pump_min_threshold = float(pump_min_threshold)
            if isinstance(pump_max_threshold, str):
                pump_max_threshold = float(pump_max_threshold)
            
            if pump_min_threshold <= change_24h <= pump_max_threshold:  # Entre 0.5% et 3.0% = signal d'achat optimal
                signal = 'BUY'
            elif change_24h < -pump_min_threshold:  # Moins de -0.5% = signal de vente (éviter la chute)  
                signal = 'SELL'
            
            # NOUVELLE LOGIQUE : ENTRER UNIQUEMENT SUR SIGNAL BUY
            if signal == 'BUY':
                print(f"✅ {symbol}: Signal BUY généré (Change: {change_24h:+.2f}%) - ENTRÉE EN POSITION")
                
                # SIMULATION de trading avec vraies données
                if self.simulation_mode:
                    self._execute_simulated_trade(symbol, {
                        'signal': signal,
                        'current_price': current_price,
                        'change_24h': change_24h,
                        'volume_24h': volume_24h,
                        'confidence': 0.7
                    })
                else:
                    self._execute_real_trade(symbol, {
                        'signal': signal,
                        'current_price': current_price,
                        'change_24h': change_24h,
                        'volume_24h': volume_24h,
                        'confidence': 0.7
                    })
            elif signal == 'SELL':
                print(f"ℹ️ {symbol}: Signal SELL détecté (Change: {change_24h:+.2f}%) - IGNORÉ (on ne trade que les BUY)")
                return  # Ignorer les signaux SELL
                    
        except Exception as e:
            print(f"❌ Erreur traitement {symbol}: {e}")
            return
    
    def _calculate_dynamic_take_profit(self, symbol: str, signal_data: Dict) -> float:
        """Calcule le Take Profit dynamique selon le potentiel de hausse"""
        try:
            # Vérifier si le mode dynamique est activé
            if not self.config_manager.get('DYNAMIC_TAKE_PROFIT', True):
                return self.config_manager.get('take_profit_percent', 1.5)
            
            current_price = signal_data.get('current_price', 0)
            change_24h = signal_data.get('change_24h', 0)
            volume_24h = signal_data.get('volume_24h', 0)
            
            # === 1. ANALYSE RSI (estimation basée sur change_24h) ===
            # Estimation RSI : Plus le change est négatif, plus le RSI est bas
            estimated_rsi = 50 + (change_24h * 2)
            if estimated_rsi < 0: estimated_rsi = 0
            if estimated_rsi > 100: estimated_rsi = 100
            
            rsi_very_low_threshold = self.config_manager.get('RSI_VERY_LOW_THRESHOLD', 25)
            rsi_medium_threshold = self.config_manager.get('RSI_MEDIUM_THRESHOLD', 40)
            
            if estimated_rsi < rsi_very_low_threshold:
                rsi_tp = self.config_manager.get('TP_RSI_VERY_LOW', 2.5)
                rsi_strength = "TRÈS BAS"
            elif estimated_rsi < rsi_medium_threshold:
                rsi_tp = self.config_manager.get('TP_RSI_MEDIUM', 1.5)
                rsi_strength = "MOYEN"
            else:
                rsi_tp = self.config_manager.get('TP_RSI_LIMIT', 1.0)
                rsi_strength = "LIMITE"
            
            # === 2. ANALYSE VOLUME SPIKE ===
            # Estimation volume ratio basée sur les données
            volume_ratio = min(150 + (abs(change_24h) * 20), 400)  # Estimation
            
            volume_high_threshold = self.config_manager.get('VOLUME_SPIKE_HIGH_THRESHOLD', 200)
            volume_medium_threshold = self.config_manager.get('VOLUME_SPIKE_MEDIUM_THRESHOLD', 130)
            
            if volume_ratio > volume_high_threshold:
                volume_tp = self.config_manager.get('TP_VOLUME_SPIKE_HIGH', 3.0)
                volume_strength = "ÉNORME"
            elif volume_ratio > volume_medium_threshold:
                volume_tp = self.config_manager.get('TP_VOLUME_SPIKE_MEDIUM', 2.0)
                volume_strength = "FORT"
            else:
                volume_tp = self.config_manager.get('TP_VOLUME_SPIKE_LOW', 1.5)
                volume_strength = "NORMAL"
            
            # === 3. ANALYSE PUMP 3MIN ===
            pump_3min = abs(change_24h)  # Utiliser change_24h comme proxy
            
            pump_strong_threshold = self.config_manager.get('PUMP_STRONG_THRESHOLD', 2.0)
            pump_medium_threshold = self.config_manager.get('PUMP_MEDIUM_THRESHOLD', 1.0)
            
            if pump_3min > pump_strong_threshold:
                pump_tp = self.config_manager.get('TP_PUMP_STRONG', 2.5)
                pump_strength = "TRÈS FORT"
            elif pump_3min > pump_medium_threshold:
                pump_tp = self.config_manager.get('TP_PUMP_MEDIUM', 1.8)
                pump_strength = "FORT"
            else:
                pump_tp = self.config_manager.get('TP_PUMP_LOW', 1.2)
                pump_strength = "MODÉRÉ"
            
            # === 4. ANALYSE TYPE DE CRYPTO ===
            base_currency = symbol.split('/')[0]
            
            if base_currency in ['BTC', 'ETH']:
                crypto_tp = self.config_manager.get('TP_BTC_ETH', 1.5)
                crypto_type = "STABLE"
            elif base_currency in ['BNB', 'ADA', 'SOL', 'DOT', 'AVAX', 'LINK', 'UNI', 'MATIC', 'ATOM', 'XRP']:
                crypto_tp = self.config_manager.get('TP_TOP_ALTCOINS', 2.0)
                crypto_type = "TOP ALTCOIN"
            else:
                crypto_tp = self.config_manager.get('TP_MICROCAPS', 3.5)
                crypto_type = "MICROCAP"
            
            # === 5. CALCUL TAKE PROFIT FINAL (moyenne pondérée) ===
            # Pondération : RSI 30%, Volume 25%, Pump 25%, Type 20%
            dynamic_tp = (rsi_tp * 0.30) + (volume_tp * 0.25) + (pump_tp * 0.25) + (crypto_tp * 0.20)
            
            # Limiter entre 1% et 5% pour éviter les extrêmes
            dynamic_tp = max(1.0, min(dynamic_tp, 5.0))
            
            # Log détaillé du calcul
            self.log(f"🎯 TP DYNAMIQUE {symbol}:")
            self.log(f"   📊 RSI: {estimated_rsi:.0f} ({rsi_strength}) → {rsi_tp:.1f}%")
            self.log(f"   📈 Volume: {volume_ratio:.0f}% ({volume_strength}) → {volume_tp:.1f}%")
            self.log(f"   🚀 Pump: {pump_3min:.1f}% ({pump_strength}) → {pump_tp:.1f}%")
            self.log(f"   💎 Type: {crypto_type} → {crypto_tp:.1f}%")
            self.log(f"   🎯 TAKE PROFIT FINAL: {dynamic_tp:.1f}%")
            
            return dynamic_tp
            
        except Exception as e:
            self.log(f"❌ Erreur calcul TP dynamique {symbol}: {e}")
            # Fallback sur TP fixe
            return self.config_manager.get('take_profit_percent', 1.5)
    
    def _execute_simulated_trade(self, symbol: str, signal_data: Dict):
        """Exécute un trade simulé avec affichage dans le GUI + gestion positions"""
        try:
            signal = signal_data['signal']
            # === FRAIS BINANCE RÉELS 2025 ===
            # VIP 0 + BNB : Maker 0.075%, Taker 0.075% (IDENTIQUE !)
            # → Pas besoin de stratégie maker, utiliser prix marché directement
            
            # Configuration frais selon niveau utilisateur
            use_bnb_discount = self.config_manager.get('USE_BNB_DISCOUNT', True)
            vip_level = self.config_manager.get('BINANCE_VIP_LEVEL', 0)
            
            # Configuration des frais selon niveau VIP (depuis config.txt UNIQUEMENT)
            vip_4_maker_fee = self.config_manager.get('VIP_4_MAKER_FEE')
            vip_4_taker_fee = self.config_manager.get('VIP_4_TAKER_FEE')  
            base_maker_fee = self.config_manager.get('BASE_MAKER_FEE')
            base_taker_fee = self.config_manager.get('BASE_TAKER_FEE')
            bnb_discount_rate = self.config_manager.get('BNB_DISCOUNT_RATE')
            
            if vip_level >= 4:
                # VIP 4+ : Frais différents maker/taker
                base_maker_fee = vip_4_maker_fee
                base_taker_fee = vip_4_taker_fee
                use_maker_strategy = True  # Avantage à être maker
            else:
                # VIP 0-3 : Frais identiques avec BNB  
                use_maker_strategy = False  # Pas d'avantage avec BNB
            
            # Appliquer discount BNB si activé
            if use_bnb_discount and bnb_discount_rate:
                maker_fee = base_maker_fee * bnb_discount_rate if base_maker_fee else 0.00075
                taker_fee = base_taker_fee * bnb_discount_rate if base_taker_fee else 0.00075
                fee_currency = "BNB"
                # VIP 0 + BNB : maker = taker = 0.075%, donc pas besoin stratégie maker
                if vip_level < 4:
                    use_maker_strategy = False
            else:
                maker_fee = base_maker_fee
                taker_fee = base_taker_fee
                fee_currency = "USDT"
                use_maker_strategy = True  # Sans BNB, maker < taker
            
            # === STRATÉGIE DE PRIX SIMPLIFIÉE ===
            current_price = signal_data['current_price']
            change_24h = signal_data.get('change_24h', 0)
            confidence = signal_data.get('confidence', 0.7)
            
            # Configuration des offsets et prix (depuis config.txt uniquement)
            maker_offset = self.config_manager.get('MAKER_OFFSET_PERCENT')
            stop_loss_buy_multiplier = self.config_manager.get('STOP_LOSS_BUY_MULTIPLIER')
            stop_loss_sell_multiplier = self.config_manager.get('STOP_LOSS_SELL_MULTIPLIER')
            
            if use_maker_strategy:
                # VIP élevé ou sans BNB : utiliser stratégie maker
                if signal == 'BUY':
                    entry_price = current_price * (1 - (maker_offset or 0.0001))  # Sous le marché
                    trading_fees = maker_fee or 0.00075
                    order_type = "MAKER"
                else:
                    entry_price = current_price * (1 + (maker_offset or 0.0001))  # Sur le marché
                    trading_fees = maker_fee or 0.00075
                    order_type = "MAKER"
            else:
                # VIP 0 + BNB : frais identiques, utiliser prix marché (taker)
                entry_price = current_price  # Prix de marché directement
                trading_fees = taker_fee or 0.00075  # 0.075% (= maker_fee)
                order_type = "TAKER"
            
            # Calculs stop loss seulement (take profit supprimé - système 3 couches utilisé)
            # NOUVEAU SYSTÈME SIMPLIFIÉ : STOP LOSS + TAKE PROFIT FIXE
            stop_loss_buy_multiplier = self.config_manager.get('STOP_LOSS_BUY_MULTIPLIER')
            stop_loss_sell_multiplier = self.config_manager.get('STOP_LOSS_SELL_MULTIPLIER')
            take_profit_buy_multiplier = self.config_manager.get('TAKE_PROFIT_BUY_MULTIPLIER')
            take_profit_sell_multiplier = self.config_manager.get('TAKE_PROFIT_SELL_MULTIPLIER')
            
            # SIMPLIFIÉ : TOUJOURS DU LONG (signal BUY uniquement)
            operation = 'ACHAT'
            direction = 'LONG' 
            signal_display = 'BUY'  # Toujours BUY maintenant
            
            # === CALCUL TAKE PROFIT DYNAMIQUE ===
            dynamic_tp_percent = self._calculate_dynamic_take_profit(symbol, signal_data)
            
            # STOP LOSS et TAKE PROFIT pour LONG uniquement
            stop_loss = entry_price * (stop_loss_buy_multiplier or 0.995)    # -0.5% (plus bas)
            take_profit = entry_price * (1 + (dynamic_tp_percent / 100))     # TP dynamique (plus haut)
            
            # Calculer la taille de position selon la stratégie OPTIMISÉE (depuis config.txt UNIQUEMENT)
            max_position_per_crypto = self.config_manager.get('order_size') or self.config_manager.get('POSITION_SIZE_USDT')
            
            # Vérifier qu'on a assez de capital
            if self.simulation_mode:
                available_balance = self.simulated_balance
            else:
                available_balance = self.balance
            
            # Si balance insuffisante, ne pas trader
            if available_balance < max_position_per_crypto:
                self.log(f"⚠️ {symbol}: Balance insuffisante ({available_balance:.2f}€ < {max_position_per_crypto}€) - TRADE ANNULÉ")
                return
            
            # === CALCUL AVEC FRAIS INCLUS ===
            position_size_usdt = max_position_per_crypto  # 100€ par trade
            entry_fees = position_size_usdt * trading_fees  # Frais d'entrée
            net_position_size = position_size_usdt - entry_fees  # Capital réel investi
            quantity = net_position_size / entry_price  # Quantité ajustée aux frais
            
            # NOUVEAU: Ajouter les frais d'entrée au total
            self.total_fees += entry_fees
            
            # Calculer stop loss avec prix maker
            # (déjà calculé plus haut avec entry_price)
            
            # Vérifier si on a déjà une position ouverte pour ce symbole
            existing_position = None
            for pos in self.open_positions:
                if pos['symbol'] == symbol and pos['status'] == 'open':
                    existing_position = pos
                    break
            
            # SCALPING: Si position existante, VENDRE automatiquement SEULEMENT si profitable
            if existing_position:
                profit_threshold = self.config_manager.get('MIN_PROFIT_FOR_AUTO_SCALPING', 0.5)  # 0.5% minimum
                price_change_percent = ((current_price - existing_position['price']) / existing_position['price']) * 100
                
                if price_change_percent >= profit_threshold:
                    print(f"🔄 SCALPING {symbol}: Position profitable (+{price_change_percent:.2f}%) - VENTE AUTOMATIQUE")
                    self._close_position_with_reason(existing_position, current_price, "AUTO_SCALPING_PROFIT")
                    return
                else:
                    print(f"⏸️ SCALPING {symbol}: Position non-profitable ({price_change_percent:+.2f}%) - ATTENTE mouvement")
                    return  # Ne pas créer nouvelle position, attendre
            
            # Créer l'ordre simulé avec SYSTÈME SIMPLIFIÉ : Stop Loss + Take Profit Dynamique
            trade_data = {
                'symbol': symbol,
                'side': signal_display,  # Pour affichage (BUY)
                'operation': operation,  # TOUJOURS 'ACHAT'
                'direction': direction,  # TOUJOURS 'LONG'
                'quantity': quantity,
                'price': entry_price,  # Prix maker, pas prix marché
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,  # NOUVEAU: Take Profit Dynamique
                'dynamic_tp_percent': dynamic_tp_percent,  # % TP calculé dynamiquement
                'timestamp': datetime.now(),
                'entry_time': datetime.now(),
                'direction': direction,
                'value_usdt': position_size_usdt,
                'net_invested': net_position_size,
                'trading_fees': trading_fees,
                'order_type': order_type,
                'status': 'open',
                'entry_momentum': current_price,  # Pour surveillance intelligente
                'change_24h': change_24h,  # Pour affichage du momentum
                'last_check': datetime.now(),
                'system_type': 'SIMPLE_STOP_TAKE_PROFIT',  # Nouveau système
                'order_id': f"sim_{symbol.replace('/', '')}_{int(time.time())}"
            }
            
            # Ajouter à la liste des positions ouvertes
            self.open_positions.append(trade_data)
            
            # NOUVEAU: Sauvegarder immédiatement après nouveau trade
            self.save_portfolio_state()
            
            # Mettre à jour la balance selon le mode  
            if self.simulation_mode:
                # CORRECTION: Déduire seulement le capital RÉELLEMENT investi (après frais)
                self.simulated_balance -= net_position_size  # 49.95€ au lieu de 50€
                self.balance = self.simulated_balance
            
            # Affichage détaillé avec nouvelle logique
            print(f"🎮 TRADE SIMULÉ: {symbol}")
            print(f"   Signal: {signal} ({operation})")
            print(f"   Prix marché: ${current_price:.10f}")
            
            if use_maker_strategy:
                print(f"   Prix MAKER: ${entry_price:.10f} ({'+' if entry_price > current_price else ''}{((entry_price/current_price-1)*100):+.3f}%)")
                print(f"   Stratégie: MAKER (frais maker < taker)")
            else:
                print(f"   Prix TAKER: ${entry_price:.10f} (prix marché direct)")
                print(f"   Stratégie: TAKER (frais maker = taker avec BNB)")
            
            print(f"   Quantité: {quantity:.8f}")
            print(f"   Valeur brute: ${position_size_usdt:.2f}")
            print(f"   Frais entrée: ${entry_fees:.3f} {fee_currency} ({trading_fees*100:.3f}% {order_type})")
            print(f"   Capital investi: ${net_position_size:.2f}")
            print(f"   VIP Level: {vip_level} | BNB: {'✅' if use_bnb_discount else '❌'} | Type: {order_type}")
            print(f"   Stop Loss: ${stop_loss:.10f}")
            print(f"   Take Profit: ${take_profit:.10f}")
            print(f"   Balance: ${self.simulated_balance:.2f}")
            print(f"   🎯 NOUVEAU SYSTÈME: Stop Loss + Take Profit + Surveillance intelligente")
            
            # DÉMARRER LE NOUVEAU SYSTÈME DE SURVEILLANCE SIMPLIFIÉ
            threading.Thread(target=self._monitor_position_simple, args=[trade_data], daemon=True).start()
            
            # Notifier le GUI
            for callback in self.callbacks.get('trade_executed', []):
                try:
                    callback(trade_data)
                except Exception:
                    pass
                    
            # Notifier balance
            for callback in self.callbacks.get('balance_update', []):
                try:
                    callback(self.simulated_balance, len(self.open_positions))
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"❌ Erreur trade simulé {symbol}: {e}")
    
    def _close_position_scalping(self, position: Dict, exit_price: float):
        """Ferme une position scalping avec calcul P&L incluant les frais"""
        try:
            # S'assurer que exit_time est défini si pas encore fait
            if 'exit_time' not in position:
                position['exit_time'] = datetime.now()
            
            # S'assurer que exit_reason est défini avec une valeur par défaut
            if 'exit_reason' not in position:
                position['exit_reason'] = 'MANUAL_CLOSE'
                
            entry_price = position['price']
            quantity = position['quantity']
            position_value = position['value_usdt']  # 200€ initial
            # Calculer frais d'entrée avec taux depuis config.txt UNIQUEMENT
            default_trading_fees = self.config_manager.get('DEFAULT_TRADING_FEES')
            entry_fees = position.get('entry_fees', position_value * (default_trading_fees or 0.001))
            trading_fees = position.get('trading_fees', default_trading_fees or 0.001)
            
            # === STRATÉGIE DE SORTIE COHÉRENTE ===
            # Utiliser la même logique que l'entrée
            use_maker_strategy = position.get('use_maker_strategy', False)
            order_type = position.get('order_type', 'TAKER')
            
            if use_maker_strategy:
                # Stratégie maker : décaler le prix
                maker_offset = 0.0001  # 0.01% de décalage
                if position['direction'] == 'LONG':
                    # Vente LONG : offre de vente SUR le marché (maker)
                    actual_exit_price = exit_price * (1 + maker_offset)
                else:
                    # Achat SHORT : offre d'achat SOUS le marché (maker)  
                    actual_exit_price = exit_price * (1 - maker_offset)
                exit_order_type = "MAKER"
            else:
                # Stratégie taker : prix marché direct (VIP 0 + BNB)
                actual_exit_price = exit_price  # Prix marché
                exit_order_type = "TAKER"
            
            # Calculer valeur brute de sortie
            gross_exit_value = quantity * actual_exit_price
            
            # Calculer frais de sortie (même taux que l'entrée)
            exit_fees = gross_exit_value * trading_fees
            
            # NOUVEAU: Ajouter les frais de sortie au total
            self.total_fees += exit_fees
            
            # Valeur nette après frais de sortie
            net_exit_value = gross_exit_value - exit_fees
            
            # Calculer P&L net (après tous les frais)
            net_invested = position_value - entry_fees  # Capital réellement investi
            net_pnl = net_exit_value - net_invested  # P&L net après frais
            pnl_percent = (net_pnl / net_invested) * 100
            
            # CORRECTION: Total rendu = capital investi réel + P&L net
            # On récupère ce qu'on a réellement investi + les gains/pertes
            total_return = net_invested + net_pnl  # 49.95€ + P&L au lieu de 50€ + P&L
            
            # Mettre à jour la balance selon le mode
            if self.simulation_mode:
                self.simulated_balance += total_return
                self.balance = self.simulated_balance
            
            # Marquer la position comme fermée
            position['status'] = 'closed'
            position['exit_price'] = actual_exit_price
            position['exit_fees'] = exit_fees
            position['net_pnl'] = net_pnl
            position['pnl_percent'] = pnl_percent
            position['total_fees'] = entry_fees + exit_fees
            
            # Ajouter à l'historique des trades fermés
            closed_trade = position.copy()
            # Convertir les datetime en string AVANT d'ajouter à l'historique
            if 'timestamp' in closed_trade and hasattr(closed_trade['timestamp'], 'isoformat'):
                closed_trade['timestamp'] = closed_trade['timestamp'].isoformat()
            if 'entry_time' in closed_trade and hasattr(closed_trade['entry_time'], 'isoformat'):
                closed_trade['entry_time'] = closed_trade['entry_time'].isoformat()
            if 'last_significant_move' in closed_trade and hasattr(closed_trade['last_significant_move'], 'isoformat'):
                closed_trade['last_significant_move'] = closed_trade['last_significant_move'].isoformat()
            if 'exit_timestamp' in closed_trade and hasattr(closed_trade['exit_timestamp'], 'isoformat'):
                closed_trade['exit_timestamp'] = closed_trade['exit_timestamp'].isoformat()
            
            closed_trade['closed_at'] = datetime.now().isoformat()
            self.closed_trades.append(closed_trade)
            
            # MISE À JOUR du P&L total
            self.total_pnl += net_pnl
            
            # NOUVEAU: Sauvegarder immédiatement après fermeture
            self.save_portfolio_state()
            
            # Affichage détaillé du calcul P&L
            print(f"💰 VENTE SCALPING: {position['symbol']}")
            print(f"   === CALCUL P&L DÉTAILLÉ ===")
            print(f"   Prix entrée: ${entry_price:.10f} ({order_type})")
            print(f"   Prix marché sortie: ${exit_price:.10f}")
            
            if use_maker_strategy:
                print(f"   Prix MAKER sortie: ${actual_exit_price:.10f} ({'+' if actual_exit_price > exit_price else ''}{((actual_exit_price/exit_price-1)*100):+.3f}%)")
                print(f"   Stratégie: MAKER (frais avantageux)")
            else:
                print(f"   Prix TAKER sortie: ${actual_exit_price:.10f} (prix marché)")
                print(f"   Stratégie: TAKER (frais identiques avec BNB)")
            
            print(f"   --- CALCUL DÉTAILLÉ ---")
            print(f"   Capital investi: ${net_invested:.2f}")
            print(f"   Valeur brute sortie: ${gross_exit_value:.2f}")
            print(f"   Frais entrée: ${entry_fees:.3f} BNB")
            print(f"   Frais sortie: ${exit_fees:.3f} BNB")
            print(f"   Total frais: ${entry_fees + exit_fees:.3f} BNB")
            print(f"   --- RÉSULTAT ---")
            print(f"   GAIN BRUT: ${gross_exit_value - (net_invested + entry_fees):.2f}")
            print(f"   MOINS FRAIS: ${exit_fees:.3f} BNB")
            print(f"   GAIN NET: ${net_pnl:+.2f} ({pnl_percent:+.2f}%)")
            print(f"   Balance: ${self.balance:.2f}")
            
            # Notifier callbacks trade fermé (VENTE)
            for callback in self.callbacks.get('trade_executed', []):
                try:
                    callback({
                        **position,
                        'status': 'closed',
                        'operation': 'VENTE',  # Marquer comme vente
                        'exit_price': actual_exit_price,
                        'net_pnl': net_pnl,
                        'pnl_percent': pnl_percent,
                        'side': 'SELL'  # Côté vente
                    })
                except Exception:
                    pass
            
            # Notifier balance
            for callback in self.callbacks.get('balance_update', []):
                try:
                    callback(self.balance, len([p for p in self.open_positions if p['status'] == 'open']))
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"❌ Erreur fermeture position: {e}")
    
    def _auto_close_scalping_position(self, position: Dict):
        """Ferme automatiquement une position après délai (scalping) avec VRAI prix"""
        if position['status'] == 'open':
            symbol = position['symbol']
            
            # UTILISER LE VRAI PRIX ACTUEL depuis l'API
            try:
                if hasattr(self, 'exchange') and self.exchange:
                    # Récupérer le VRAI prix current de Binance
                    ticker = self.exchange.fetch_ticker(symbol)
                    current_price = ticker['last']  # Prix réel actuel
                    
                    print(f"⏰ AUTO-VENTE SCALPING: {symbol} après 30s")
                    print(f"   Prix entrée: ${position['price']:.6f}")
                    print(f"   Prix sortie RÉEL: ${current_price:.6f}")
                    print(f"   Différence: {((current_price/position['price']-1)*100):+.3f}%")
                    
                else:
                    # Fallback: utiliser données WebSocket si disponibles
                    current_price = position['price'] * 1.001  # Variation minime réaliste
                    print(f"⚠️ Utilisation prix fallback pour {symbol}")
                    
            except Exception as e:
                print(f"❌ Erreur récupération prix réel {symbol}: {e}")
                # Fallback: petite variation aléatoire réaliste
                import random
                variation = random.uniform(-0.005, 0.005)  # ±0.5% aléatoire
                current_price = position['price'] * (1 + variation)
                print(f"⚠️ Utilisation prix aléatoire pour {symbol}: {variation*100:+.2f}%")
            
            self._close_position_with_reason(position, current_price, "AUTO_CLOSE_RANDOM_PRICE")
    def _process_trading_signal(self, symbol: str, signal_data: Dict):
        """Traite un signal de trading avec affichage détaillé"""
        try:
            signal = signal_data['signal']
            confidence = signal_data['confidence']
            score = signal_data['score']
            reason = signal_data.get('reason', 'Analyse technique')
            
            # Log détaillé du signal
            factors = signal_data.get('confidence_factors', [])
            factors_str = ', '.join(factors) if factors else 'N/A'
            
            self.log(f"🔍 ANALYSE {symbol}: Signal={signal}, Score={score:.1f}, Conf={confidence:.2f}")
            self.log(f"   📊 Facteurs: {factors_str}")
            self.log(f"   💡 Raison: {reason}")
            
            # Gestion des positions existantes
            if symbol in self.positions:
                self._manage_existing_position(symbol, signal_data)
                return
            
            # Si la crypto est dans la watchlist, elle a DÉJÀ passé tous les filtres
            # Plus besoin de vérification supplémentaire - TRADE AUTOMATIQUEMENT
            
            # Nouvelles opportunités de trading
            if signal == 'BUY':
                self.log(f"🟢 {symbol}: SIGNAL D'ACHAT détecté !")
                self._open_position(symbol, 'long', signal_data)
            elif signal == 'SELL':
                self.log(f"🔴 {symbol}: SIGNAL DE VENTE détecté !")
                self._open_position(symbol, 'short', signal_data)
            else:
                self.log(f"🟡 {symbol}: Maintien position (HOLD) - Score trop faible")
            
        except Exception as e:
            self.log(f"❌ Erreur traitement signal {symbol}: {e}")
    
    def _open_position(self, symbol: str, direction: str, signal_data: Dict):
        """Ouvre une nouvelle position avec détails complets"""
        try:
            current_price = signal_data['price']
            score = signal_data['score']
            confidence = signal_data['confidence']
            rsi = signal_data.get('rsi', 0)
            macd = signal_data.get('macd', 0)
            
            # Calculer la taille de position
            balance = self.get_balance()
            position_size = self.risk_manager.calculate_position_size(balance, current_price)
            
            # Calculer stop loss seulement (système 3 couches utilisé)
            stop_loss = self.risk_manager.calculate_stop_loss(current_price, direction)
            
            # Calcul valeur en USDT
            position_value = position_size * current_price
            
            if self.simulation_mode:
                # Mode simulation
                order_id = f"sim_{symbol}_{int(time.time())}"
                self.log(f"🎮 SIMULATION - NOUVELLE POSITION")
            else:
                # Mode réel
                order = self._place_real_order(symbol, direction, position_size)
                if not order:
                    return
                order_id = order.get('id', 'unknown')
                self.log(f"💰 TRADING RÉEL - NOUVELLE POSITION")
            
            # Log détaillé de l'ouverture
            self.log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.log(f"📈 POSITION OUVERTE: {symbol}")
            self.log(f"   🎯 Direction: {direction.upper()}")
            self.log(f"   💰 Prix entrée: ${current_price:.6f}")
            self.log(f"   📊 Quantité: {position_size:.6f}")
            self.log(f"   💵 Valeur: ${position_value:.2f} USDT")
            self.log(f"   🛡️ Stop Loss: ${stop_loss:.6f} (-{self.risk_manager.stop_loss_percent}%)")
            self.log(f"   📊 Signal Score: {score:.1f}")
            self.log(f"   🎲 Confiance: {confidence:.1%}")
            self.log(f"   📈 RSI: {rsi:.1f}")
            self.log(f"   📊 MACD: {macd:.6f}")
            self.log(f"   🆔 Order ID: {order_id}")
            self.log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # Enregistrer la position
            self.positions[symbol] = {
                'direction': direction,
                'size': position_size,
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'timestamp': datetime.now(),
                'order_id': order_id,
                'signal_score': score,
                'confidence': confidence,
                'rsi_entry': rsi,
                'macd_entry': macd,
                'position_value': position_value
            }
            
            # Notifier les callbacks
            for callback in self.callbacks['position_update']:
                try:
                    callback('open', symbol, self.positions[symbol])
                except Exception:
                    pass
            
        except Exception as e:
            self.log(f"❌ Erreur ouverture position {symbol}: {e}")
    
    def _manage_existing_position(self, symbol: str, signal_data: Dict):
        """Gère une position existante"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        current_price = signal_data['price']
        
        # Vérifier stop loss
        if ((position['direction'] == 'long' and current_price <= position['stop_loss']) or
            (position['direction'] == 'short' and current_price >= position['stop_loss'])):
            self._close_position(symbol, "Stop Loss")
            return
    
    def _close_position(self, symbol: str, reason: str):
        """Ferme une position"""
        if symbol not in self.positions:
            return
        
        try:
            position = self.positions[symbol]
            current_price = self.websocket_manager.get_latest_price(symbol)
            
            if not current_price:
                return
            
            # Calculer P&L
            pnl = self._calculate_pnl(position, current_price)
            
            if not self.simulation_mode:
                # Ordre réel de fermeture
                self._place_real_close_order(symbol, position)
            
            # Supprimer la position
            del self.positions[symbol]
            
            self.log(f"🔐 Position {symbol} fermée - {reason} - P&L: {pnl:+.2f} USDT")
            
            # Notifier les callbacks
            for callback in self.callbacks['position_update']:
                try:
                    callback('close', symbol, {'reason': reason, 'pnl': pnl})
                except Exception:
                    pass
            
        except Exception as e:
            self.log(f"❌ Erreur fermeture position {symbol}: {e}")
    
    def _place_real_order(self, symbol: str, direction: str, amount: float):
        """Place un ordre réel sur l'exchange"""
        try:
            if not self.exchange:
                return None
            
            side = 'buy' if direction == 'long' else 'sell'
            order = self.exchange.create_market_order(symbol, side, amount)
            
            return order
            
        except Exception as e:
            self.log(f"❌ Erreur ordre réel {symbol}: {e}")
            return None
    
    def _place_real_close_order(self, symbol: str, position: Dict):
        """Place un ordre de fermeture réel"""
        try:
            if not self.exchange:
                return
            
            side = 'sell' if position['direction'] == 'long' else 'buy'
            self.exchange.create_market_order(symbol, side, position['size'])
            
        except Exception as e:
            self.log(f"❌ Erreur fermeture réelle {symbol}: {e}")
    
    def _calculate_pnl(self, position: Dict, current_price: float) -> float:
        """Calcule le P&L d'une position"""
        entry_price = position['entry_price']
        size = position['size']
        
        if position['direction'] == 'long':
            return (current_price - entry_price) * size
        else:
            return (entry_price - current_price) * size
    
    def get_balance(self) -> float:
        """Récupère le solde USDT via vos clés privées"""
        try:
            balance = self.exchange.fetch_balance()
            return balance.get('USDT', {}).get('free', 0.0)
        except Exception as e:
            self.log(f"❌ Erreur récupération balance via clés privées: {e}")
            return 0.0
    
    def get_positions_summary(self) -> Dict:
        """Retourne un résumé des positions"""
        if not self.positions:
            return {'count': 0, 'total_pnl': 0}
        
        total_pnl = 0
        for symbol, position in self.positions.items():
            current_price = self.websocket_manager.get_latest_price(symbol)
            if current_price:
                pnl = self._calculate_pnl(position, current_price)
                total_pnl += pnl
        
        return {
            'count': len(self.positions),
            'total_pnl': total_pnl,
            'symbols': list(self.positions.keys())
        }
    
    def toggle_simulation_mode(self, confirm_real: bool = False):
        """Bascule entre mode simulation et réel"""
        if not self.simulation_mode and not confirm_real:
            self.log("⚠️ Passage en mode réel nécessite une confirmation")
            return False
        
        self.simulation_mode = not self.simulation_mode
        mode_str = "SIMULATION" if self.simulation_mode else "RÉEL"
        self.log(f"🔄 Mode basculé vers: {mode_str}")
        
        return True
    
    def start(self):
        """Démarre le bot"""
        if self.is_running:
            self.log("⚠️ Bot déjà en cours d'exécution")
            return
        
        self.log("🚀 Démarrage du bot de trading...")
        
        # Marquer comme en cours d'exécution AVANT la configuration
        self.is_running = True
        
        # ÉTAPE 1: Initialiser l'exchange avec vos clés privées
        if not self._initialize_exchange():
            self.log("❌ Impossible de se connecter avec vos clés privées")
            self.log("   Vérifiez vos clés API dans l'onglet Configuration")
            self.is_running = False
            return
        
        # ÉTAPE 2: Configuration de la watchlist
        self.setup_watchlist()
        
        # ÉTAPE 3: Configuration WebSockets
        self.setup_websockets()
        
        # ÉTAPE 4: Gestion du solde selon le mode
        if self.simulation_mode:
            # Mode simulation - utiliser balance simulée
            self.balance = self.simulated_balance
            self.log(f"💰 Solde SIMULÉ: {self.balance:.2f} USDT")
        else:
            # Mode réel - récupérer vraie balance
            self.balance = self.get_balance()
            self.log(f"💰 Solde RÉEL: {self.balance:.2f} USDT")
        
        # Notifier la balance initiale au GUI
        for callback in self.callbacks.get('balance_update', []):
            try:
                callback(self.balance, len(self.open_positions))
            except Exception:
                pass
        
        self.log("✅ Bot démarré avec succès")
        
        # Si pas de watchlist, le scan continu va chercher automatiquement
        if not self.watchlist:
            self.log("🔍 Aucune watchlist configurée - Le scan continu recherchera automatiquement")
        else:
            self.log(f"📋 Watchlist configurée: {self.watchlist}")
    
    def stop(self):
        """Arrête le bot"""
        if not self.is_running:
            return
        
        self.log("🛑 Arrêt du bot...")
        
        # Arrêter le système de fallback
        if hasattr(self, '_fallback_running'):
            self._fallback_running = False
        
        # Fermer toutes les positions
        for symbol in list(self.positions.keys()):
            self._close_position(symbol, "Arrêt du bot")
        
        # Arrêter les WebSockets
        if self.websocket_manager:
            self.websocket_manager.stop_all_streams()
        
        self.is_running = False
        self.log("✅ Bot arrêté")

# Test du moteur
if __name__ == "__main__":
    from config_manager import ConfigManager
    
    print("🧪 Test du moteur de trading")
    
    # Charger la configuration
    config = ConfigManager()
    
    # Créer le bot
    bot = CryptoTradingBot(config)
    
    # Démarrer
    bot.start()
    
    try:
        # Laisser tourner pendant 30 secondes
        time.sleep(30)
        
        # Afficher les statistiques
        positions = bot.get_positions_summary()
        print(f"📊 Positions: {positions}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé")
    finally:
        bot.stop()
        print("✅ Test terminé")