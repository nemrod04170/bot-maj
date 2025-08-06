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
WebSocket Manager Optimisé - Données Temps Réel Binance
Architecture légère et performante
"""

import json
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Callable, Optional
import websocket
from collections import defaultdict, deque
import pandas as pd

class BinanceWebSocketManager:
    """Gestionnaire WebSocket optimisé pour Binance - Temps réel"""
    
    def __init__(self, testnet: bool = False):
        self.testnet = testnet
        
        # URLs WebSocket
        if testnet:
            self.base_url = "wss://testnet.binance.vision/ws/"
            print("🧪 Mode TESTNET WebSocket")
        else:
            self.base_url = "wss://stream.binance.com:9443/ws/"
            print("🚀 Mode PRODUCTION WebSocket")
        
        # État des connexions - PERSISTANT
        self.ws_connections = {}
        self.is_running = False
        self.connection_status = {}
        self.should_reconnect = True
        self.current_symbols = []
        self.restart_lock = threading.Lock()  # Éviter les redémarrages multiples
        
        # Mécanisme de reconnexion
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # secondes
        self.last_ping = None
        self.ping_interval = 30  # secondes
        
        # Stockage données temps réel
        self.price_data = {}  # Prix instantanés
        self.kline_data = defaultdict(lambda: deque(maxlen=100))  # OHLCV
        self.volume_data = {}  # Volumes 24h
        self.change_data = {}  # Changements 24h
        
        # Callbacks pour notifications
        self.callbacks = {
            'price_update': [],
            'kline_update': [],
            'volume_update': [],
            'connection_status': []
        }
        
        # Threads actifs
        self.threads = []
        
        # Statistiques
        self.stats = {
            'messages_received': 0,
            'last_update': None,
            'symbols_tracked': 0,
            'uptime_start': datetime.now(),
            'reconnections': 0,
            'last_disconnection': None
        }
        
        logging.info("WebSocket Manager initialisé avec mécanisme de reconnexion")
    
    def add_callback(self, event_type: str, callback: Callable):
        """Ajoute un callback pour les événements"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def start_price_streams(self, symbols: List[str]):
        """Démarre les streams de prix pour une liste de symboles avec reconnexion automatique"""
        if not symbols:
            print("⚠️ Aucun symbole fourni")
            return
        
        self.current_symbols = symbols.copy()
        self.should_reconnect = True
        self.reconnect_attempts = 0
        
        self._start_connection()
    
    def _start_connection(self):
        """Démarre une connexion WebSocket avec gestion d'erreurs robuste"""
        if not self.current_symbols:
            return
        
        try:
            # Convertir symboles (BTC/USDT → btcusdt)
            binance_symbols = [symbol.replace('/', '').lower() for symbol in self.current_symbols]
            
            # Créer l'URL du stream combiné
            streams = []
            for symbol in binance_symbols:
                streams.append(f"{symbol}@ticker")
                streams.append(f"{symbol}@kline_1h")  # Klines 1h par défaut
            
            stream_url = self.base_url + "/".join(streams)
            
            print(f"🔗 Connexion WebSocket: {len(self.current_symbols)} symboles (tentative {self.reconnect_attempts + 1})")
            print(f"📡 URL: {stream_url[:100]}...")
            
            def on_message(ws, message):
                try:
                    self.stats['messages_received'] += 1
                    self.stats['last_update'] = datetime.now()
                    self.last_ping = datetime.now()  # Marquer activité
                    
                    data = json.loads(message)
                    
                    if 'stream' in data:
                        stream_name = data['stream']
                        symbol_raw = stream_name.split('@')[0].upper()
                        # Reconvertir format (BTCUSDT → BTC/USDT)
                        symbol = f"{symbol_raw[:-4]}/{symbol_raw[-4:]}"
                        
                        if '@ticker' in stream_name:
                            self._process_ticker_data(symbol, data['data'])
                        elif '@kline' in stream_name:
                            self._process_kline_data(symbol, data['data'])
                
                except Exception as e:
                    logging.error(f"Erreur traitement message WebSocket: {e}")
            
            def on_error(ws, error):
                logging.error(f"Erreur WebSocket: {error}")
                self.connection_status['main'] = 'error'
                self.stats['last_disconnection'] = datetime.now()
                self._notify_callbacks('connection_status', 'error')
                
                # Programmer une reconnexion si nécessaire
                if self.should_reconnect:
                    self._schedule_reconnection()
            
            def on_close(ws, close_status_code, close_msg):
                logging.warning(f"WebSocket fermé: {close_status_code} - {close_msg}")
                self.connection_status['main'] = 'closed'
                self.stats['last_disconnection'] = datetime.now()
                self._notify_callbacks('connection_status', 'closed')
                
                # Programmer une reconnexion si nécessaire
                if self.should_reconnect:
                    self._schedule_reconnection()
            
            def on_open(ws):
                logging.info(f"✅ WebSocket connecté - {len(self.current_symbols)} symboles")
                self.connection_status['main'] = 'connected'
                self.stats['symbols_tracked'] = len(self.current_symbols)
                self.reconnect_attempts = 0  # Reset compteur de reconnexions
                self.last_ping = datetime.now()
                self._notify_callbacks('connection_status', 'connected')
                
                # Démarrer le monitoring de connexion
                self._start_connection_monitor()
            
            # Créer connexion WebSocket
            ws = websocket.WebSocketApp(
                stream_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            self.ws_connections['main'] = ws
            
            # Démarrer dans un thread
            thread = threading.Thread(target=ws.run_forever, daemon=True)
            thread.start()
            self.threads.append(thread)
            
            self.is_running = True
            
        except Exception as e:
            logging.error(f"Erreur création WebSocket: {e}")
            if self.should_reconnect:
                self._schedule_reconnection()
    
    def _schedule_reconnection(self):
        """Programme une reconnexion automatique"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logging.error(f"❌ Nombre maximum de tentatives de reconnexion atteint ({self.max_reconnect_attempts})")
            self.should_reconnect = False
            return
        
        self.reconnect_attempts += 1
        delay = min(self.reconnect_delay * self.reconnect_attempts, 60)  # Max 60 secondes
        
        logging.info(f"🔄 Reconnexion programmée dans {delay} secondes (tentative {self.reconnect_attempts})")
        
        def reconnect():
            time.sleep(delay)
            if self.should_reconnect:
                self.stats['reconnections'] += 1
                logging.info(f"🔄 Tentative de reconnexion {self.reconnect_attempts}")
                self._start_connection()
        
        thread = threading.Thread(target=reconnect, daemon=True)
        thread.start()
        self.threads.append(thread)
    
    def _start_connection_monitor(self):
        """Démarre le monitoring de la connexion avec ping/pong"""
        def monitor():
            while self.is_connected() and self.should_reconnect:
                try:
                    # Vérifier si on a reçu des données récemment
                    if self.last_ping:
                        time_since_ping = (datetime.now() - self.last_ping).total_seconds()
                        if time_since_ping > self.ping_interval * 2:  # 2x l'intervalle = problème
                            logging.warning(f"⚠️ Aucune donnée reçue depuis {time_since_ping:.1f}s - Reconnexion")
                            self.connection_status['main'] = 'stale'
                            self._notify_callbacks('connection_status', 'stale')
                            
                            # Forcer la reconnexion
                            if 'main' in self.ws_connections:
                                try:
                                    self.ws_connections['main'].close()
                                except:
                                    pass
                            break
                    
                    time.sleep(self.ping_interval)
                    
                except Exception as e:
                    logging.error(f"Erreur monitoring connexion: {e}")
                    break
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        self.threads.append(thread)
    
    def _process_ticker_data(self, symbol: str, ticker_data: Dict):
        """Traite les données ticker (prix, volume, changement)"""
        try:
            # DEBUG: Vérifier les données reçues
            if not ticker_data:
                return
            
            # Vérifier les champs critiques avec gestion plus robuste
            price = 0
            volume_24h = 0
            quote_volume_24h = 0
            price_change_24h = 0
            
            # Extraction plus robuste des données
            if 'c' in ticker_data:
                try:
                    price = float(ticker_data['c'])
                except (ValueError, TypeError):
                    return
            elif 'last' in ticker_data:
                try:
                    price = float(ticker_data['last'])
                except (ValueError, TypeError):
                    return
            else:
                return
                
            # Vérifier que le prix est valide
            if price <= 0:
                print(f"🔧 DEBUG: Prix invalide ({price}) pour {symbol} - données: {ticker_data}")
                return
            
            # Extraction des autres données avec valeurs par défaut
            try:
                volume_24h = float(ticker_data.get('v', 0))
                quote_volume_24h = float(ticker_data.get('q', 0))
                price_change_24h = float(ticker_data.get('P', 0))
            except (ValueError, TypeError):
                # Utiliser des valeurs par défaut si extraction échoue
                volume_24h = 1000000  # Volume par défaut
                quote_volume_24h = 1000000
                price_change_24h = 0
            
            # Stocker les données
            self.price_data[symbol] = {
                'price': price,
                'timestamp': datetime.now()
            }
            
            self.volume_data[symbol] = {
                'volume_24h': quote_volume_24h,  # Volume en USDT
                'timestamp': datetime.now()
            }
            
            self.change_data[symbol] = {
                'change_24h': price_change_24h,
                'timestamp': datetime.now()
            }
            
            # Notifier le moteur de trading avec les vraies données
            trading_data = {
                'current_price': price,
                'volume_24h': quote_volume_24h,
                'change_24h': price_change_24h,
                'symbol': symbol,
                'timestamp': datetime.now()
            }
            
            # Dernière vérification avant envoi
            if trading_data['current_price'] > 0:
                self._notify_callbacks('price_update', trading_data)
            else:
                print(f"🔧 DEBUG: Prix toujours invalide ({trading_data['current_price']}) pour {symbol} après traitement")
            
        except Exception as e:
            # Log plus silencieux pour éviter le spam
            pass
    
    def _process_kline_data(self, symbol: str, kline_data: Dict):
        """Traite les données kline (OHLCV)"""
        try:
            kline = kline_data['k']
            
            ohlcv = {
                'timestamp': pd.to_datetime(kline['t'], unit='ms'),
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c']),
                'volume': float(kline['v']),
                'is_closed': kline['x']  # True si bougie fermée
            }
            
            # Stocker dans la queue
            if kline['x']:  # Seulement les bougies fermées
                self.kline_data[symbol].append(ohlcv)
            
            # Notifier les callbacks
            self._notify_callbacks('kline_update', {
                'symbol': symbol,
                'kline': ohlcv
            })
            
        except Exception as e:
            logging.error(f"Erreur traitement kline {symbol}: {e}")
    
    def _notify_callbacks(self, event_type: str, data: any = None):
        """Notifie tous les callbacks d'un type d'événement"""
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                print(f"❌ Erreur callback {event_type}: {e}")
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Récupère le dernier prix d'un symbole"""
        data = self.price_data.get(symbol)
        return data['price'] if data else None
    
    def get_latest_volume(self, symbol: str) -> Optional[float]:
        """Récupère le dernier volume 24h d'un symbole"""
        data = self.volume_data.get(symbol)
        return data['volume_24h'] if data else None
    
    def get_latest_change(self, symbol: str) -> Optional[float]:
        """Récupère le dernier changement 24h d'un symbole"""
        data = self.change_data.get(symbol)
        return data['change_24h'] if data else None
    
    def get_price_data_all(self) -> Dict[str, Dict]:
        """Récupère toutes les données de prix"""
        result = {}
        for symbol in self.price_data.keys():
            result[symbol] = {
                'price': self.get_latest_price(symbol),
                'volume_24h': self.get_latest_volume(symbol),
                'change_24h': self.get_latest_change(symbol),
                'timestamp': self.price_data[symbol]['timestamp']
            }
        return result
    
    def get_kline_dataframe(self, symbol: str) -> pd.DataFrame:
        """Convertit les klines en DataFrame pandas"""
        if symbol not in self.kline_data or not self.kline_data[symbol]:
            return pd.DataFrame()
        
        klines = list(self.kline_data[symbol])
        df = pd.DataFrame(klines)
        return df.sort_values('timestamp')
    
    def get_connection_status(self) -> Dict[str, str]:
        """Retourne le statut des connexions"""
        return self.connection_status.copy()
    
    def get_statistics(self) -> Dict:
        """Retourne les statistiques détaillées"""
        uptime = datetime.now() - self.stats['uptime_start']
        
        return {
            'messages_received': self.stats['messages_received'],
            'symbols_tracked': self.stats['symbols_tracked'],
            'last_update': self.stats['last_update'],
            'uptime_seconds': uptime.total_seconds(),
            'is_running': self.is_running,
            'connections': len(self.ws_connections),
            'price_symbols': len(self.price_data),
            'kline_symbols': len(self.kline_data),
            'reconnections': self.stats.get('reconnections', 0),
            'reconnect_attempts': self.reconnect_attempts,
            'connection_health': self.get_connection_health()
        }
    
    def stop_all_streams(self):
        """Arrête tous les streams WebSocket"""
        self.is_running = False
        self.should_reconnect = False
        
        for name, ws in self.ws_connections.items():
            try:
                ws.close()
                logging.info(f"WebSocket {name} fermé")
            except Exception as e:
                logging.error(f"Erreur fermeture WebSocket {name}: {e}")
        
        self.ws_connections.clear()
        self.connection_status.clear()
        
        print("🛑 Tous les WebSockets arrêtés")
    
    def restart_streams(self, symbols: List[str]):
        """Redémarre les streams avec de nouveaux symboles"""
        print("🔄 Redémarrage des WebSockets...")
        self.stop_all_streams()
        time.sleep(2)  # Attendre la fermeture complète
        self.start_price_streams(symbols)
    
    def stop_all_streams(self):
        """Arrête tous les streams WebSocket"""
        self.is_running = False
        self.should_reconnect = False
        
        for name, ws in self.ws_connections.items():
            try:
                ws.close()
                logging.info(f"WebSocket {name} fermé")
            except Exception as e:
                logging.error(f"Erreur fermeture WebSocket {name}: {e}")
        
        self.ws_connections.clear()
        self.connection_status.clear()
        
        print("🛑 Tous les WebSockets arrêtés")
    
    def is_connected(self) -> bool:
        """Vérifie si au moins une connexion est active"""
        status = self.connection_status.get('main', 'disconnected')
        return status == 'connected'
    
    def get_connection_health(self) -> Dict:
        """Retourne l'état de santé de la connexion"""
        now = datetime.now()
        
        return {
            'is_connected': self.is_connected(),
            'status': self.connection_status.get('main', 'disconnected'),
            'reconnect_attempts': self.reconnect_attempts,
            'messages_received': self.stats['messages_received'],
            'last_update': self.stats['last_update'],
            'last_disconnection': self.stats.get('last_disconnection'),
            'reconnections_count': self.stats.get('reconnections', 0),
            'uptime_seconds': (now - self.stats['uptime_start']).total_seconds() if self.stats['uptime_start'] else 0,
            'symbols_tracked': len(self.current_symbols),
            'should_reconnect': self.should_reconnect
        }
    
    def is_connected(self) -> bool:
        """Vérifie si au moins une connexion est active"""
        return self.connection_status.get('main') == 'connected'
    
    def get_symbols_tracked(self) -> List[str]:
        """Retourne la liste des symboles trackés"""
        return list(self.price_data.keys())

# Test du WebSocket
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🧪 Test du WebSocket Manager")
    
    # Créer le gestionnaire
    ws_manager = BinanceWebSocketManager(testnet=False)
    
    # Callbacks de test
    def on_price_update(data):
        symbol = data['symbol']
        price = data['price']
        change = data['change_24h']
        print(f"💰 {symbol}: ${price:.4f} ({change:+.2f}%)")
    
    def on_connection_status(status):
        print(f"🔗 Connexion: {status}")
    
    # Ajouter callbacks
    ws_manager.add_callback('price_update', on_price_update)
    ws_manager.add_callback('connection_status', on_connection_status)
    
    # Test avec quelques symboles
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    ws_manager.start_price_streams(test_symbols)
    
    try:
        # Test pendant 30 secondes
        time.sleep(30)
        
        # Afficher statistiques
        stats = ws_manager.get_statistics()
        print(f"\n📊 Statistiques:")
        print(f"   Messages reçus: {stats['messages_received']}")
        print(f"   Symboles trackés: {stats['symbols_tracked']}")
        print(f"   Temps de fonctionnement: {stats['uptime_seconds']:.1f}s")
        
        # Afficher données actuelles
        all_data = ws_manager.get_price_data_all()
        print(f"\n💰 Données actuelles:")
        for symbol, data in all_data.items():
            print(f"   {symbol}: ${data['price']:.4f} ({data['change_24h']:+.2f}%)")
    
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé")
    finally:
        ws_manager.stop_all_streams()
        print("✅ Test terminé")