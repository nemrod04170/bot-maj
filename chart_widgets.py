#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widgets de Graphiques Temps Réel
Graphiques intégrés pour l'interface GUI
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import pandas as pd
import numpy as np
import time
import threading
import random
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional

class MiniChart:
    """Mini graphique intégré pour une crypto"""
    
    def __init__(self, parent, symbol: str, width: int = 200, height: int = 120):
        self.parent = parent
        self.symbol = symbol
        self.width = width
        self.height = height
        
        # Données du graphique
        self.price_history = deque(maxlen=60)  # 1 minute de données
        self.time_history = deque(maxlen=60)
        
        # État actuel
        self.current_price = 0.0
        self.change_24h = 0.0
        self.volume_24h = 0.0
        self.signal = "HOLD"
        self.signal_score = 0
        
        # Créer l'interface
        self._create_widget()
        
        # Configuration du graphique
        self._setup_chart()
    
    def _create_widget(self):
        """Crée le widget principal"""
        # Frame principal
        self.frame = tk.Frame(self.parent, bg='#2d2d2d', relief='raised', bd=1)
        self.frame.pack(side='left', padx=5, pady=5)
        
        # Header avec symbole et prix
        self.header_frame = tk.Frame(self.frame, bg='#2d2d2d')
        self.header_frame.pack(fill='x', padx=5, pady=2)
        
        # Symbole
        self.symbol_label = tk.Label(
            self.header_frame,
            text=self.symbol,
            font=('Arial', 10, 'bold'),
            fg='white',
            bg='#2d2d2d'
        )
        self.symbol_label.pack(side='left')
        
        # Prix actuel
        self.price_label = tk.Label(
            self.header_frame,
            text="$0.0000",
            font=('Arial', 9),
            fg='white',
            bg='#2d2d2d'
        )
        self.price_label.pack(side='right')
        
        # Frame pour le graphique
        self.chart_frame = tk.Frame(self.frame, bg='#2d2d2d')
        self.chart_frame.pack(padx=2, pady=2)
        
        # Footer avec infos
        self.footer_frame = tk.Frame(self.frame, bg='#2d2d2d')
        self.footer_frame.pack(fill='x', padx=5, pady=2)
        
        # Changement 24h
        self.change_label = tk.Label(
            self.footer_frame,
            text="0.00%",
            font=('Arial', 8),
            fg='gray',
            bg='#2d2d2d'
        )
        self.change_label.pack(side='left')
        
        # Signal
        self.signal_label = tk.Label(
            self.footer_frame,
            text="HOLD",
            font=('Arial', 8, 'bold'),
            fg='orange',
            bg='#2d2d2d'
        )
        self.signal_label.pack(side='right')
    
    def _setup_chart(self):
        """Configure le graphique matplotlib"""
        # Créer la figure
        self.fig = Figure(
            figsize=(self.width/100, self.height/100),
            dpi=100,
            facecolor='#2d2d2d'
        )
        
        # Créer le subplot
        self.ax = self.fig.add_subplot(111, facecolor='#1a1a1a')
        
        # Style du graphique
        self.ax.tick_params(colors='gray', labelsize=6)
        self.ax.spines['bottom'].set_color('gray')
        self.ax.spines['top'].set_color('gray')
        self.ax.spines['left'].set_color('gray')
        self.ax.spines['right'].set_color('gray')
        
        # Supprimer les labels des axes
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Ligne de prix
        self.price_line, = self.ax.plot([], [], color='#00ff88', linewidth=1.5)
        
        # Canvas tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()
    
    def update_price(self, price: float, volume_24h: float, change_24h: float):
        """Met à jour le prix et les données"""
        self.current_price = price
        self.volume_24h = volume_24h
        self.change_24h = change_24h
        
        # Ajouter aux historiques
        now = datetime.now()
        self.price_history.append(price)
        self.time_history.append(now)
        
        # Mettre à jour l'affichage
        self._update_labels()
        self._update_chart()
    
    def update_signal(self, signal: str, score: float):
        """Met à jour le signal de trading"""
        self.signal = signal
        self.signal_score = score
        self._update_signal_display()
    
    def _update_labels(self):
        """Met à jour les labels textuels"""
        # Prix avec formatage intelligent
        if self.current_price >= 1:
            price_text = f"${self.current_price:.2f}"
        elif self.current_price >= 0.01:
            price_text = f"${self.current_price:.4f}"
        else:
            price_text = f"${self.current_price:.6f}"
        
        self.price_label.config(text=price_text)
        
        # Changement 24h avec couleur
        change_text = f"{self.change_24h:+.2f}%"
        change_color = '#00ff88' if self.change_24h >= 0 else '#ff4444'
        self.change_label.config(text=change_text, fg=change_color)
    
    def _update_signal_display(self):
        """Met à jour l'affichage du signal"""
        signal_colors = {
            'BUY': '#00ff88',
            'SELL': '#ff4444',
            'HOLD': '#ffaa00'
        }
        
        color = signal_colors.get(self.signal, '#gray')
        self.signal_label.config(text=self.signal, fg=color)
    
    def _update_chart(self):
        """Met à jour le graphique"""
        if len(self.price_history) < 2:
            return
        
        try:
            # Préparer les données
            prices = list(self.price_history)
            x_data = range(len(prices))
            
            # Mettre à jour la ligne
            self.price_line.set_data(x_data, prices)
            
            # Ajuster les limites
            if prices:
                min_price = min(prices)
                max_price = max(prices)
                price_range = max_price - min_price
                
                if price_range > 0:
                    self.ax.set_ylim(min_price - price_range * 0.1, 
                                   max_price + price_range * 0.1)
                else:
                    # Prix stable
                    self.ax.set_ylim(min_price * 0.999, max_price * 1.001)
                
                self.ax.set_xlim(0, len(prices) - 1)
            
            # Redessiner
            self.canvas.draw()
            
        except Exception as e:
            print(f"Erreur mise à jour graphique {self.symbol}: {e}")

class CryptoChartsPanel:
    """Panel contenant tous les mini-graphiques"""
    
    def __init__(self, parent, max_charts: int = 6):
        self.parent = parent
        self.max_charts = max_charts
        self.charts = {}  # symbol -> MiniChart
        
        # Créer le panel principal
        self._create_panel()
    
    def _create_panel(self):
        """Crée le panel principal"""
        # Frame principal avec scrollbar si nécessaire
        self.main_frame = tk.Frame(self.parent, bg='#1a1a1a')
        self.main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Titre
        title_label = tk.Label(
            self.main_frame,
            text="📈 GRAPHIQUES PRIX TEMPS RÉEL",
            font=('Arial', 12, 'bold'),
            fg='white',
            bg='#1a1a1a'
        )
        title_label.pack(pady=(0, 10))
        
        # Frame pour les graphiques (grille)
        self.charts_frame = tk.Frame(self.main_frame, bg='#1a1a1a')
        self.charts_frame.pack(fill='both', expand=True)
    
    def add_chart(self, symbol: str) -> bool:
        """Ajoute un graphique pour un symbole"""
        if symbol in self.charts:
            return True
        
        if len(self.charts) >= self.max_charts:
            print(f"⚠️ Limite de {self.max_charts} graphiques atteinte")
            return False
        
        try:
            # Créer le mini-graphique
            chart = MiniChart(self.charts_frame, symbol)
            self.charts[symbol] = chart
            
            print(f"✅ Graphique ajouté: {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur création graphique {symbol}: {e}")
            return False
    
    def remove_chart(self, symbol: str):
        """Supprime un graphique"""
        if symbol in self.charts:
            self.charts[symbol].frame.destroy()
            del self.charts[symbol]
            print(f"🗑️ Graphique supprimé: {symbol}")
    
    def update_chart_price(self, symbol: str, price: float, volume_24h: float, change_24h: float):
        """Met à jour le prix d'un graphique"""
        if symbol in self.charts:
            self.charts[symbol].update_price(price, volume_24h, change_24h)
    
    def update_chart_signal(self, symbol: str, signal: str, score: float):
        """Met à jour le signal d'un graphique"""
        if symbol in self.charts:
            self.charts[symbol].update_signal(signal, score)
    
    def clear_all_charts(self):
        """Supprime tous les graphiques"""
        for symbol in list(self.charts.keys()):
            self.remove_chart(symbol)
    
    def update_watchlist(self, symbols: List[str]):
        """Met à jour la liste des graphiques selon la watchlist"""
        # Supprimer les graphiques non présents dans la nouvelle liste
        current_symbols = set(self.charts.keys())
        new_symbols = set(symbols)
        
        # Supprimer les anciens
        for symbol in current_symbols - new_symbols:
            self.remove_chart(symbol)
        
        # Ajouter les nouveaux
        for symbol in new_symbols - current_symbols:
            self.add_chart(symbol)
        
        print(f"📊 Graphiques mis à jour: {len(self.charts)} actifs")
    
    def get_active_symbols(self) -> List[str]:
        """Retourne la liste des symboles avec graphiques actifs"""
        return list(self.charts.keys())

class LargeChart:
    """Graphique principal détaillé (optionnel)"""
    
    def __init__(self, parent, width: int = 600, height: int = 300):
        self.parent = parent
        self.width = width
        self.height = height
        
        # Données
        self.price_data = []
        self.volume_data = []
        self.time_data = []
        
        # Créer l'interface
        self._create_widget()
        self._setup_chart()
    
    def _create_widget(self):
        """Crée le widget principal"""
        self.frame = tk.Frame(self.parent, bg='#2d2d2d', relief='raised', bd=2)
        self.frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Titre
        self.title_label = tk.Label(
            self.frame,
            text="📊 GRAPHIQUE PRINCIPAL",
            font=('Arial', 12, 'bold'),
            fg='white',
            bg='#2d2d2d'
        )
        self.title_label.pack(pady=5)
    
    def _setup_chart(self):
        """Configure le graphique principal"""
        # Figure matplotlib
        self.fig = Figure(
            figsize=(self.width/100, self.height/100),
            dpi=100,
            facecolor='#2d2d2d'
        )
        
        # Sous-graphiques
        self.ax_price = self.fig.add_subplot(211, facecolor='#1a1a1a')  # Prix
        self.ax_volume = self.fig.add_subplot(212, facecolor='#1a1a1a')  # Volume
        
        # Style
        for ax in [self.ax_price, self.ax_volume]:
            ax.tick_params(colors='gray', labelsize=8)
            for spine in ax.spines.values():
                spine.set_color('gray')
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def update_data(self, symbol: str, price_df: pd.DataFrame):
        """Met à jour les données du graphique principal"""
        if price_df.empty:
            return
        
        try:
            # Préparer les données
            times = price_df['timestamp']
            prices = price_df['close']
            volumes = price_df['volume']
            
            # Graphique des prix
            self.ax_price.clear()
            self.ax_price.plot(times, prices, color='#00ff88', linewidth=2)
            self.ax_price.set_title(f"{symbol} - Prix", color='white', fontsize=10)
            self.ax_price.tick_params(colors='gray', labelsize=8)
            
            # Graphique des volumes
            self.ax_volume.clear()
            self.ax_volume.bar(times, volumes, color='#666666', alpha=0.7)
            self.ax_volume.set_title("Volume", color='white', fontsize=10)
            self.ax_volume.tick_params(colors='gray', labelsize=8)
            
            # Ajuster l'espacement
            self.fig.tight_layout()
            
            # Redessiner
            self.canvas.draw()
            
        except Exception as e:
            print(f"Erreur mise à jour graphique principal: {e}")

# Test des widgets
if __name__ == "__main__":
    print("🧪 Test des widgets de graphiques")
    
    root = tk.Tk()
    root.title("Test Graphiques Crypto")
    root.geometry("800x600")
    root.configure(bg='#1a1a1a')
    
    # Créer le panel de graphiques
    charts_panel = CryptoChartsPanel(root, max_charts=6)
    
    # Ajouter quelques graphiques de test
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    for symbol in test_symbols:
        charts_panel.add_chart(symbol)
    
    # Simuler des mises à jour de prix
    def simulate_price_updates():
        def update_prices():
            while True:
                for symbol in test_symbols:
                    # Prix simulé
                    base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 300
                    price = base_price * (1 + random.uniform(-0.02, 0.02))
                    volume = random.uniform(1000000, 10000000)
                    change = random.uniform(-5, 5)
                    
                    charts_panel.update_chart_price(symbol, price, volume, change)
                    
                    # Signal simulé
                    signals = ['BUY', 'SELL', 'HOLD']
                    signal = random.choice(signals)
                    score = random.uniform(0, 100)
                    
                    charts_panel.update_chart_signal(symbol, signal, score)
                
                time.sleep(2)  # Mise à jour toutes les 2 secondes
        
        thread = threading.Thread(target=update_prices, daemon=True)
        thread.start()
    
    # Démarrer les mises à jour simulées
    simulate_price_updates()
    
    root.mainloop()