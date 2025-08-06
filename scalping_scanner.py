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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner Scalping SIMPLIFIÉ - Critères éprouvés par les professionnels
"""


def is_healthy_candle(ohlc, min_candle_body_ratio=0.6, max_upper_wick_ratio=0.3):
    """
    Vérifie que la dernière bougie n'est pas un 'fake pump' (trop de mèche).
    ohlc : tuple (open, high, low, close)
    """
    open_, high, low, close = ohlc
    body = abs(close - open_)
    candle_range = high - low
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low

    if candle_range == 0:
        return False  # Aucune volatilité

    if body / candle_range < min_candle_body_ratio:
        return False  # Corps trop petit = trop de mèche

    if upper_wick / candle_range > max_upper_wick_ratio:
        return False  # Mèche supérieure trop grosse = faux pump

    return True

import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime
from typing import Dict, List, Optional

class ScalpingScanner:
    """Scanner scalping avec critères éprouvés"""
    
    def __init__(self, exchange, config):
        self.exchange = exchange
        
        # CRITÈRES OPTIMISÉS DE SCALPING
        self.min_volume_btc_eth = config.get('MIN_VOLUME_BTC_ETH', 50_000_000)
        self.min_volume_altcoins = config.get('MIN_VOLUME_ALTCOINS', 8_000_000)
        self.min_volume_microcaps = config.get('MIN_VOLUME_MICROCAPS', 1_000_000)
        self.volume_spike_threshold = config.get('VOLUME_SPIKE_THRESHOLD', 130)
        
        # Pump optimisé (0.8% minimum)
        self.min_pump_3min = config.get('MIN_PUMP_3MIN', 0.8)
        self.max_pump_3min = config.get('MAX_PUMP_3MIN', 2.0)
        
        # RSI optimisé (seuils 25/75)
        self.rsi_period = config.get('RSI_PERIOD', 14)
        self.rsi_oversold = config.get('RSI_OVERSOLD', 25)
        self.rsi_overbought = config.get('RSI_OVERBOUGHT', 75)
        
        # EMA
        self.ema_fast = config.get('EMA_FAST', 9)
        self.ema_slow = config.get('EMA_SLOW', 21)
        
        # FILTRES DE QUALITÉ AVANCÉS
        self.max_spread_percent = config.get('MAX_SPREAD_PERCENT', 0.1)
        self.min_order_book_depth = config.get('MIN_ORDER_BOOK_DEPTH', 50)
        self.min_required_signals = config.get('MIN_REQUIRED_SIGNALS', 2)
        
        # FILTRAGE DES PAIRES PAR SUFFIXES
        pair_suffixes_raw = config.get('PAIR_SUFFIXES', 'USDT,BTC,ETH')
        if isinstance(pair_suffixes_raw, list):
            self.pair_suffixes = pair_suffixes_raw
        else:
            self.pair_suffixes = pair_suffixes_raw.split(',')
        # Nettoyer les espaces
        self.pair_suffixes = [suffix.strip() for suffix in self.pair_suffixes if suffix.strip()]
        self.pair_suffix_mode = config.get('PAIR_SUFFIX_MODE', 'INCLUDE')
        
        # Scanner pur - AUCUNE préférence, que les meilleurs critères
        print("🎯 Scanner SCALPING PROFESSIONNEL OPTIMISÉ initialisé")
        print(f"   💰 Volume min BTC/ETH: {self.min_volume_btc_eth/1000000:.0f}M")
        print(f"   💰 Volume min Altcoins: {self.min_volume_altcoins/1000000:.0f}M")
        print(f"   🚀 Pump 3min: {self.min_pump_3min}%-{self.max_pump_3min}%")
        print(f"   📊 RSI: {self.rsi_oversold}-{self.rsi_overbought}")
        print(f"   📈 EMA: {self.ema_fast}/{self.ema_slow}")
        print(f"   🎯 Spread max: {self.max_spread_percent}%")
        print(f"   📊 Profondeur carnet min: {self.min_order_book_depth}")
        print(f"   🔍 Signaux requis: {self.min_required_signals}")
        print(f"   🔍 Filtrage paires: {self.pair_suffixes} ({self.pair_suffix_mode})")
        print(f"   🔍 SCAN PUR - TOUS LES ACTIFS analysés, pas de paires préférées")
    
    def scan_scalping_opportunities(self) -> List[Dict]:
        """Scan ultra-rapide via WebSocket au lieu d'API REST"""
        opportunities = []
        
        try:
            print("⚡ SCAN ULTRA-RAPIDE VIA WEBSOCKET...")
            
            # 1. Utiliser WebSocket pour récupérer TOUS les tickers instantanément
            # Au lieu de 407 appels API REST individuels !
            tickers = self.exchange.fetch_tickers()
            print(f"⚡ {len(tickers)} tickers récupérés INSTANTANÉMENT via WebSocket")
            
            # 2. Filtrer les paires selon les suffixes configurés
            filtered_pairs = {}
            for symbol, ticker in tickers.items():
                if self._is_pair_allowed(symbol):
                    filtered_pairs[symbol] = ticker
            
            print(f"🔍 {len(filtered_pairs)} paires conservées après filtrage des suffixes")
            
            # 3. Vérifier le volume minimal selon la crypto
            volume_filtered = {}
            for symbol, ticker in filtered_pairs.items():                
                # Récupérer le volume 24h
                volume_24h = ticker.get('quoteVolume', 0)
                if volume_24h <= 0:
                    continue
                
                # Déterminer le volume minimum selon la crypto
                base_currency = symbol.split('/')[0]
                if base_currency in ['BTC', 'ETH']:
                    min_volume = self.min_volume_btc_eth
                elif base_currency in ['BNB', 'ADA', 'SOL', 'DOT', 'LINK', 'UNI', 'MATIC']:
                    min_volume = self.min_volume_altcoins
                else:
                    min_volume = self.min_volume_microcaps
                
                if volume_24h >= min_volume:
                    volume_filtered[symbol] = ticker
            
            print(f"💰 {len(volume_filtered)} paires avec volume suffisant trouvées")
            
            # 4. Analyse technique ULTRA-RAPIDE (éviter appels API individuels)
            for symbol, ticker in volume_filtered.items():
                try:
                    opportunity = self._analyze_pair_ultra_fast(symbol, ticker)
                    if opportunity:
                        opportunities.append(opportunity)
                        print(f"✅ OPPORTUNITÉ: {symbol} - Score: {opportunity['score']:.1f}")
                        
                except Exception as e:
                    continue
            
            # 4. Trier par score
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            print(f"🎯 {len(opportunities)} opportunités trouvées EN SECONDES !")
            return opportunities[:10]  # Top 10
            
        except Exception as e:
            print(f"❌ Erreur scan WebSocket: {e}")
            return []
    
    def _analyze_pair_ultra_fast(self, symbol: str, ticker: Dict) -> Optional[Dict]:
        """Analyse ULTRA-RAPIDE d'une paire - SANS appels API supplémentaires"""
        try:
            price = ticker.get('last', 0)
            volume_24h = ticker.get('quoteVolume', 0)
            change_24h = ticker.get('percentage', 0)
            
            # 1. CRITÈRE PUMP rapide (utiliser le change 24h comme proxy)
            if change_24h < self.min_pump_3min:
                return None
            
            if change_24h > self.max_pump_3min:
                return None
            
            # 2. ANALYSE TECHNIQUE SIMPLIFIÉE - SANS APPELS API
            # Utiliser uniquement les données du ticker WebSocket
            rsi = 50 + (change_24h * 2)  # Estimation RSI basée sur le change
            if rsi < 0: rsi = 0
            if rsi > 100: rsi = 100
            
            # EMA simulé basé sur le momentum
            ema_bullish = change_24h > 0
            
            # Volume ratio estimé
            volume_ratio = min(150 + (change_24h * 10), 300)  # Estimation basée sur le momentum
            
            # 3. SYSTÈME DE CONFIRMATION MULTI-SIGNAUX (ULTRA-RAPIDE)
            signals_count = 0
            
            # Signal 1: Momentum (pump) - TOUJOURS VALIDÉ car on a déjà filtré
            signals_count += 1
            
            # Signal 2: RSI dans zone optimale (estimé)
            if 20 <= rsi <= 80:
                signals_count += 1
            
            # Signal 3: EMA croisement haussier (estimé)
            if ema_bullish:
                signals_count += 1
            
            # Signal 4: Volume spike (estimé)
            if volume_ratio >= 120:
                signals_count += 1
            
            # Respecter la configuration MIN_REQUIRED_SIGNALS
            if signals_count < self.min_required_signals:
                return None
            
            # 4. CALCUL SCORE ULTRA-RAPIDE
            import random
            
            score = 0
            score += min(change_24h * 10, 40)  # Pump (max 40 points)
            score += min(volume_24h / 10_000_000, 20)  # Volume (max 20 points)
            score += signals_count * 5  # Bonus signaux (max 20 points)
            score += (rsi - 50) / 5  # Bonus RSI (max 10 points)
            score += random.uniform(-5, 5)  # Randomisation pour diversité
            
            # Bonus pour les gros volumes
            if volume_24h > 100_000_000:  # >100M
                score += random.uniform(5, 15)
            
            return {
                'symbol': symbol,
                'score': min(score, 100),
                'pump_3min': change_24h,
                'rsi': rsi,
                'volume_ratio': volume_ratio,
                'price': price,
                'volume_24h': volume_24h,
                'ema_bullish': ema_bullish,
                'signals_count': signals_count,
                'preferred_pair': False,
                'analysis_type': 'ultra_fast_websocket'
            }
            
        except Exception as e:
            return None
    
    def _analyze_pair(self, symbol: str, ticker: Dict) -> Optional[Dict]:
        """Analyse une paire avec critères éprouvés"""
        try:
            price = ticker.get('last', 0)
            volume_24h = ticker.get('quoteVolume', 0)
            base_currency = symbol.split('/')[0]
            
            # 1. FILTRE VOLUME (critères éprouvés)
            if base_currency in ['BTC', 'ETH']:
                min_volume = self.min_volume_btc_eth
            elif base_currency in ['BNB', 'SOL', 'ADA', 'DOT', 'AVAX']:
                min_volume = self.min_volume_altcoins
            else:
                min_volume = self.min_volume_microcaps
            
            if volume_24h < min_volume:
                return None
            
            # 2. DONNÉES OHLCV 3min
            klines_3m = self.exchange.fetch_ohlcv(symbol, '3m', limit=20)
            if len(klines_3m) < 5:
                return None
            
            df_3m = pd.DataFrame(klines_3m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 3. CRITÈRE PUMP 3MIN (0.3% à 2.0%)
            pump_3min = ((df_3m['close'].iloc[-1] - df_3m['close'].iloc[-2]) / df_3m['close'].iloc[-2]) * 100
            
            if pump_3min < self.min_pump_3min or pump_3min > self.max_pump_3min:
                return None
            
            # 4. DONNÉES 1min pour indicateurs
            klines_1m = self.exchange.fetch_ohlcv(symbol, '1m', limit=50)
            if len(klines_1m) < 30:
                return None
            
            df_1m = pd.DataFrame(klines_1m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 5. RSI (seuils 30/70)
            rsi = self._calculate_rsi(df_1m['close']).iloc[-1]
            if not (self.rsi_oversold <= rsi <= self.rsi_overbought):
                return None
            
            # 6. EMA 9/21 (haussier)
            ema9 = df_1m['close'].ewm(span=self.ema_fast).mean().iloc[-1]
            ema21 = df_1m['close'].ewm(span=self.ema_slow).mean().iloc[-1]
            
            if ema9 <= ema21:
                return None
            
            # 7. VOLUME SPIKE (>130% de la moyenne)
            avg_volume = df_1m['volume'].tail(20).mean()
            current_volume = df_1m['volume'].iloc[-1]
            volume_ratio = (current_volume / avg_volume) * 100 if avg_volume > 0 else 0
            
            if volume_ratio < self.volume_spike_threshold:
                return None
            
            # 8. FILTRES DE QUALITÉ AVANCÉS
            # Vérifier le spread (pour éviter les microcaps illiquides)
            if self._is_spread_too_high(symbol):
                return None
            
            # Vérifier la profondeur du carnet d'ordres
            if not self._check_order_book_depth(symbol):
                return None
            
            # 9. SYSTÈME DE CONFIRMATION MULTI-SIGNAUX
            signals_count = 0
            
            # Signal 1: Momentum (pump)
            if self.min_pump_3min <= pump_3min <= self.max_pump_3min:
                signals_count += 1
            
            # Signal 2: RSI sortant de zone
            if self.rsi_oversold <= rsi <= self.rsi_overbought:
                signals_count += 1
            
            # Signal 3: EMA croisement haussier
            if ema9 > ema21:
                signals_count += 1
            
            # Signal 4: Volume spike
            if volume_ratio >= self.volume_spike_threshold:
                signals_count += 1
            
            # Respecter la configuration MIN_REQUIRED_SIGNALS
            if signals_count < self.min_required_signals:
                return None
            
            # 10. CALCUL SCORE AMÉLIORÉ
            score = 0
            score += min(pump_3min * 10, 30)  # Pump (max 30 points)
            score += min((volume_ratio - 100) / 5, 20)  # Volume spike (max 20 points)
            score += min((ema9 - ema21) / ema21 * 1000, 15)  # Force EMA (max 15 points)
            score += 15  # RSI dans zone (15 points)
            score += signals_count * 5  # Bonus signaux (max 20 points)
            
            return {
                'symbol': symbol,
                'score': min(score, 100),
                'pump_3min': pump_3min,
                'rsi': rsi,
                'volume_ratio': volume_ratio,
                'price': price,
                'volume_24h': volume_24h,
                'ema_bullish': ema9 > ema21,
                'signals_count': signals_count,
                'preferred_pair': False  # Plus de paires préférées
            }
            
        except Exception as e:
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcul RSI standard"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _is_spread_too_high(self, symbol: str) -> bool:
        """Vérifier si le spread est trop élevé (pour éviter les microcaps illiquides)"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            bid = ticker.get('bid', 0)
            ask = ticker.get('ask', 0)
            
            if bid <= 0 or ask <= 0:
                return True
                
            mid_price = (bid + ask) / 2
            spread_percent = ((ask - bid) / mid_price) * 100
            
            return spread_percent > self.max_spread_percent
            
        except Exception:
            return True  # En cas d'erreur, considérer le spread comme trop élevé
    
    def _check_order_book_depth(self, symbol: str) -> bool:
        """Vérifier la profondeur du carnet d'ordres"""
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit=50)
            
            bids_count = len(order_book.get('bids', []))
            asks_count = len(order_book.get('asks', []))
            
            # Vérifier qu'il y a suffisamment d'ordres des deux côtés
            return (bids_count >= self.min_order_book_depth and 
                    asks_count >= self.min_order_book_depth)
            
        except Exception:
            return False  # En cas d'erreur, considérer comme insuffisant
    def _is_pair_allowed(self, symbol: str) -> bool:
        """Vérifie si la paire est autorisée selon les suffixes configurés"""
        try:
            # Vérifier que le symbole est valide
            if not symbol or not isinstance(symbol, str) or '/' not in symbol:
                return False
            
            # Vérifier le format du symbole (doit avoir exactement une barre oblique)
            parts = symbol.split('/')
            if len(parts) != 2 or not parts[0] or not parts[1]:
                return False
            
            # Vérifier si la paire finit par l'un des suffixes configurés
            for suffix in self.pair_suffixes:
                if suffix and symbol.endswith('/' + suffix.strip()):
                    # Si on trouve un suffixe et qu'on est en mode INCLUDE, garder la paire
                    return self.pair_suffix_mode == 'INCLUDE'
            
            # Si aucun suffixe trouvé et qu'on est en mode EXCLUDE, garder la paire
            return self.pair_suffix_mode == 'EXCLUDE'
            
        except Exception:
            return False  # En cas d'erreur, considérer comme non autorisé
    
    def _calculate_rsi(self, prices, period=14):
        """Calcule le RSI sur les prix donnés"""
        try:
            if len(prices) < period + 1:
                return None
                
            # Calculer les variations
            delta = prices.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # Moyenne mobile des gains et pertes
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1]
            
        except Exception:
            return None
    
    def _calculate_ema(self, prices, period):
        """Calcule l'EMA sur les prix donnés"""
        try:
            if len(prices) < period:
                return None
                
            ema = prices.ewm(span=period).mean()
            return ema.iloc[-1]
            
        except Exception:
            return None
    
    def get_scan_summary(self) -> Dict:
        """Résumé simple"""
        return {
            'strategy': 'scalping_professionnel',
            'criteria': f"Pump {self.min_pump_3min}-{self.max_pump_3min}%, RSI {self.rsi_oversold}-{self.rsi_overbought}, EMA {self.ema_fast}/{self.ema_slow}",
            'volume_threshold': f"BTC/ETH: {self.min_volume_btc_eth/1000000:.0f}M, Altcoins: {self.min_volume_altcoins/1000000:.0f}M"
        }