from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
import os
load_dotenv()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface GUI améliorée pour bot de trading scalping
Avec onglet Configuration complet et aperçu scan
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
from config_manager import ConfigManager
from crypto_bot_engine import CryptoTradingBot

class ScalpingBotGUI:
    """Interface graphique complète pour le bot scalping"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 BOT SCALPING PROFESSIONNEL")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Configuration
        self.config_manager = ConfigManager()
        self.bot = None
        self.bot_running = False
        
        # Variables pour scan aperçu
        self.last_scan_stats = {}
        self.last_opportunities = []
        
        self.setup_gui()
        self.load_config_to_gui()
        
        # Auto-start si configuré
        if self.config_manager.get('AUTO_START_BOT', False):
            self.root.after(2000, self.auto_start_bot)  # Démarrer après 2 secondes
    
    def setup_gui(self):
        """Configuration de l'interface graphique"""
        
        # Notebook principal
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Onglet Trading
        self.trading_frame = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(self.trading_frame, text="🎯 TRADING SCALPING")
        
        # Onglet Configuration
        self.config_frame = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(self.config_frame, text="⚙️ CONFIGURATION")
        
        # Initialiser les onglets
        self.setup_trading_tab()
        self.setup_config_tab()
        
        # Charger la configuration après création des onglets
        self.root.after(100, self.load_config_to_gui)
    
    def setup_trading_tab(self):
        """Configurer l'onglet de trading"""
        # Frame de contrôle
        control_frame = tk.Frame(self.trading_frame, bg='#2d2d2d', relief='raised', bd=2)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Bouton Start/Stop
        self.control_button = tk.Button(
            control_frame,
            text="🚀 DÉMARRER SCALPING",
            command=self.toggle_bot,
            bg='#00aa44', fg='white',
            font=('Arial', 12, 'bold'),
            height=2, width=20
        )
        self.control_button.pack(side='left', padx=10, pady=10)
        
        # Bouton Reset Simulation / Vente Positions (selon le mode)
        self.reset_button = tk.Button(
            control_frame,
            text="🔄 RESET SIMULATION",
            command=self.reset_simulation,
            bg='#ff6600', fg='white',
            font=('Arial', 10, 'bold'),
            height=2, width=18
        )
        self.reset_button.pack(side='left', padx=5, pady=10)
        
        # Status
        self.status_label = tk.Label(
            control_frame,
            text="📴 BOT ARRÊTÉ",
            bg='#2d2d2d', fg='#ff4444',
            font=('Arial', 11, 'bold')
        )
        self.status_label.pack(side='left', padx=20, pady=10)
        
        # WebSocket status
        self.websocket_label = tk.Label(
            control_frame,
            text="🔴 WEBSOCKET DÉCONNECTÉ",
            bg='#2d2d2d', fg='#ff4444',
            font=('Arial', 10)
        )
        self.websocket_label.pack(side='right', padx=10, pady=10)
        
        # Exchange status
        self.exchange_label = tk.Label(
            control_frame,
            text="📡 Binance: 🔴 DÉCONNECTÉ",
            bg='#2d2d2d', fg='#ff4444',
            font=('Arial', 10)
        )
        self.exchange_label.pack(side='right', padx=10, pady=10)
        
        # Frame principal avec 2 colonnes
        main_frame = tk.Frame(self.trading_frame, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Colonne gauche - Compteurs scan détaillés (comme l'ancien)
        left_frame = tk.Frame(main_frame, bg='#2d2d2d', relief='raised', bd=2)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        tk.Label(left_frame, text="📊 COMPTEURS SCAN", font=('Arial', 12, 'bold'), 
                fg='white', bg='#2d2d2d').pack(pady=10)
        
        # Compteurs détaillés comme l'ancien GUI
        self.scan_total_label = tk.Label(
            left_frame, text="Total Binance: 0", 
            fg='white', bg='#2d2d2d'
        )
        self.scan_total_label.pack(anchor='w', padx=10, pady=2)
        
        self.scan_usdt_label = tk.Label(
            left_frame, text="Paires acceptées: 0", 
            fg='white', bg='#2d2d2d'
        )
        self.scan_usdt_label.pack(anchor='w', padx=10, pady=2)
        
        self.scan_filtered_label = tk.Label(
            left_frame, text="Après filtres: 0", 
            fg='white', bg='#2d2d2d'
        )
        self.scan_filtered_label.pack(anchor='w', padx=10, pady=2)
        
        self.scan_selected_label = tk.Label(
            left_frame, text="Sélectionnées: 0", 
            fg='#00ff88', bg='#2d2d2d', font=('Arial', 9, 'bold')
        )
        self.scan_selected_label.pack(anchor='w', padx=10, pady=2)
        
        # Critères de scan
        self.scan_criteria_label = tk.Label(
            left_frame, text="Volume ≥2M, Pump ≥0.5%, RSI 40-80", 
            fg='#aaaaaa', bg='#2d2d2d', font=('Arial', 8)
        )
        self.scan_criteria_label.pack(anchor='w', padx=10, pady=5)
        
        # Dernière mise à jour
        self.last_scan_label = tk.Label(
            left_frame, text="Dernier scan: Jamais", 
            fg='#aaaaaa', bg='#2d2d2d', font=('Arial', 8)
        )
        self.last_scan_label.pack(anchor='w', padx=10, pady=2)
        
        # Historique des trades fermés
        tk.Label(left_frame, text="📊 HISTORIQUE TRADES FERMÉS", font=('Arial', 10, 'bold'), 
                fg='white', bg='#2d2d2d').pack(pady=(20, 5))
        
        self.trades_history_text = tk.Text(
            left_frame,
            height=15, width=50,
            bg='#1a1a1a', fg='#cccccc',
            insertbackground='white',
            font=('Courier', 9)
        )
        self.trades_history_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Initialiser l'historique
        self.closed_trades = []  # Liste des trades fermés
        self.trades_history_text.insert(1.0, "🔄 Aucun trade fermé pour le moment...\n")
        
        # Colonne droite - Dashboard de Trading Professionnel
        right_frame = tk.Frame(main_frame, bg='#1a1a1a', relief='raised', bd=2)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # === HEADER DASHBOARD ===
        header_frame = tk.Frame(right_frame, bg='#333333', height=50)
        header_frame.pack(fill='x', padx=5, pady=(5, 10))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📊 DASHBOARD DE TRADING", 
                font=('Arial', 14, 'bold'), fg='#00ff88', bg='#333333').pack(pady=15)
        
        # === SECTION PORTEFEUILLE ===
        portfolio_frame = tk.LabelFrame(right_frame, text="💰 PORTEFEUILLE", 
                                      font=('Arial', 10, 'bold'), fg='#ffaa00', bg='#2d2d2d',
                                      relief='groove', bd=2)
        portfolio_frame.pack(fill='x', padx=10, pady=5)
        
        # Balance disponible
        balance_frame = tk.Frame(portfolio_frame, bg='#2d2d2d')
        balance_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(balance_frame, text="💵 Balance Disponible:", 
                font=('Arial', 10), fg='#cccccc', bg='#2d2d2d').pack(side='left')
        
        self.balance_label = tk.Label(
            balance_frame, text="1000.00 USDT",
            fg='#ffaa00', bg='#2d2d2d',
            font=('Arial', 11, 'bold')
        )
        self.balance_label.pack(side='right')
        
        # Valeur totale portefeuille
        total_frame = tk.Frame(portfolio_frame, bg='#2d2d2d')
        total_frame.pack(fill='x', padx=10, pady=(0,5))
        
        tk.Label(total_frame, text="📈 Valeur Totale:", 
                font=('Arial', 10), fg='#cccccc', bg='#2d2d2d').pack(side='left')
        
        self.total_value_label = tk.Label(
            total_frame, text="1000.00 USDT",
            fg='#00aaff', bg='#2d2d2d',
            font=('Arial', 11, 'bold')
        )
        self.total_value_label.pack(side='right')
        
        # P&L Global
        pnl_frame = tk.Frame(portfolio_frame, bg='#2d2d2d')
        pnl_frame.pack(fill='x', padx=10, pady=(0,10))
        
        tk.Label(pnl_frame, text="💹 P&L Total:", 
                font=('Arial', 10), fg='#cccccc', bg='#2d2d2d').pack(side='left')
        
        self.pnl_label = tk.Label(
            pnl_frame, text="+0.00 USDT (0.0%)",
            fg='#00ff88', bg='#2d2d2d',
            font=('Arial', 11, 'bold')
        )
        self.pnl_label.pack(side='right')
        
        # Frais totaux
        fees_frame = tk.Frame(portfolio_frame, bg='#2d2d2d')
        fees_frame.pack(fill='x', padx=10, pady=(0,10))
        
        tk.Label(fees_frame, text="💳 Frais Totaux:", 
                font=('Arial', 10), fg='#cccccc', bg='#2d2d2d').pack(side='left')
        
        self.fees_label = tk.Label(
            fees_frame, text="-0.00 USDT",
            fg='#ff8800', bg='#2d2d2d',
            font=('Arial', 11, 'bold')
        )
        self.fees_label.pack(side='right')
        
        # === SECTION STATISTIQUES ===
        stats_frame = tk.LabelFrame(right_frame, text="📊 STATISTIQUES", 
                                  font=('Arial', 10, 'bold'), fg='#00aaff', bg='#2d2d2d',
                                  relief='groove', bd=2)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        # Grid pour les stats (2 colonnes)
        stats_grid = tk.Frame(stats_frame, bg='#2d2d2d')
        stats_grid.pack(fill='x', padx=10, pady=10)
        
        # Colonne gauche stats
        left_stats = tk.Frame(stats_grid, bg='#2d2d2d')
        left_stats.pack(side='left', fill='both', expand=True)
        
        # Positions ouvertes
        positions_frame = tk.Frame(left_stats, bg='#2d2d2d')
        positions_frame.pack(fill='x', pady=2)
        
        tk.Label(positions_frame, text="🔓 Positions Ouvertes:", 
                font=('Arial', 9), fg='#cccccc', bg='#2d2d2d').pack(side='left')
        
        self.positions_count_label = tk.Label(
            positions_frame, text="0",
            fg='#ff8800', bg='#2d2d2d',
            font=('Arial', 10, 'bold')
        )
        self.positions_count_label.pack(side='right')
        
        # Total trades
        trades_frame = tk.Frame(left_stats, bg='#2d2d2d')
        trades_frame.pack(fill='x', pady=2)
        
        tk.Label(trades_frame, text="🔢 Total Trades:", 
                font=('Arial', 9), fg='#cccccc', bg='#2d2d2d').pack(side='left')
        
        self.trades_count_label = tk.Label(
            trades_frame, text="0",
            fg='#cccccc', bg='#2d2d2d',
            font=('Arial', 10, 'bold')
        )
        self.trades_count_label.pack(side='right')
        
        # Colonne droite stats
        right_stats = tk.Frame(stats_grid, bg='#2d2d2d')
        right_stats.pack(side='right', fill='both', expand=True)
        
        # Taux de succès
        winrate_frame = tk.Frame(right_stats, bg='#2d2d2d')
        winrate_frame.pack(fill='x', pady=2)
        
        tk.Label(winrate_frame, text="🎯 Taux Succès:", 
                font=('Arial', 9), fg='#cccccc', bg='#2d2d2d').pack(side='left')
        
        self.winrate_label = tk.Label(
            winrate_frame, text="0.0%",
            fg='#00ff88', bg='#2d2d2d',
            font=('Arial', 10, 'bold')
        )
        self.winrate_label.pack(side='right')
        
        # Mode trading
        mode_frame = tk.Frame(right_stats, bg='#2d2d2d')
        mode_frame.pack(fill='x', pady=2)
        
        tk.Label(mode_frame, text="🎮 Mode:", 
                font=('Arial', 9), fg='#cccccc', bg='#2d2d2d').pack(side='left')
        
        self.mode_label = tk.Label(
            mode_frame, text="SIMULATION",
            fg='#88aaff', bg='#2d2d2d',
            font=('Arial', 10, 'bold')
        )
        self.mode_label.pack(side='right')
        
        # === SECTION POSITIONS OUVERTES ===
        positions_main_frame = tk.LabelFrame(right_frame, text="🔓 POSITIONS OUVERTES", 
                                           font=('Arial', 10, 'bold'), fg='#ff8800', bg='#2d2d2d',
                                           relief='groove', bd=2)
        positions_main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Zone de texte pour positions avec style amélioré
        positions_canvas_frame = tk.Frame(positions_main_frame, bg='#2d2d2d')
        positions_canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.positions_text = tk.Text(
            positions_canvas_frame,
            height=8, width=50,
            bg='#1a1a1a', fg='#cccccc',
            insertbackground='white',
            font=('Courier', 9),
            relief='sunken', bd=2,
            wrap=tk.WORD
        )
        
        # Scrollbar pour positions
        positions_scrollbar = tk.Scrollbar(positions_canvas_frame, command=self.positions_text.yview)
        self.positions_text.config(yscrollcommand=positions_scrollbar.set)
        
        self.positions_text.pack(side='left', fill='both', expand=True)
        positions_scrollbar.pack(side='right', fill='y')
        
        # Message initial
        self.positions_text.insert(1.0, "🚀 Démarrez le bot pour voir les positions\n\n")
        self.positions_text.config(state='disabled')
        
        # Positions
        tk.Label(right_frame, text="📈 POSITIONS OUVERTES", font=('Arial', 10, 'bold'), 
                fg='white', bg='#2d2d2d').pack(pady=(20, 5))
        
        self.positions_text = scrolledtext.ScrolledText(
            right_frame,
            height=20, width=50,
            bg='#1a1a1a', fg='white',
            insertbackground='white',
            font=('Courier', 9)
        )
        self.positions_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Logs en bas
        log_frame = tk.Frame(self.trading_frame, bg='#2d2d2d', relief='raised', bd=2)
        log_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(log_frame, text="📋 LOGS BOT", font=('Arial', 10, 'bold'), 
                fg='white', bg='#2d2d2d').pack(pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=6, bg='#1a1a1a', fg='#aaaaaa',
            insertbackground='white',
            font=('Courier', 8)
        )
        self.log_text.pack(fill='x', padx=10, pady=5)
    
    def setup_config_tab(self):
        """Configuration de l'onglet Configuration complet"""
        
        # Frame principal avec scroll
        canvas = tk.Canvas(self.config_frame, bg='#1a1a1a')
        scrollbar = ttk.Scrollbar(self.config_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1a1a1a')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Variables de configuration
        self.config_vars = {}
        
        # Section API
        self.create_config_section(scrollable_frame, "🔑 CONFIGURATION API", [
            ('API_KEY', 'Clé API Binance:', 'entry', 40),
            ('API_SECRET', 'Clé secrète:', 'entry', 40),
            ('TESTNET_MODE', 'Mode Testnet:', 'bool'),
            ('SIMULATION_MODE', 'Mode Simulation:', 'bool')
        ])
        
        # Section Frais Binance
        self.create_config_section(scrollable_frame, "💰 FRAIS BINANCE", [
            ('USE_BNB_DISCOUNT', 'Utiliser discount BNB:', 'bool'),
            ('BINANCE_VIP_LEVEL', 'Niveau VIP Binance:', 'int')
        ])
        
        # Section Timeframes
        self.create_config_section(scrollable_frame, "⏰ TIMEFRAMES", [
            ('TIMEFRAME', 'Timeframe principal:', 'entry', 10),
            ('CONFIRMATION_TIMEFRAME', 'Timeframe confirmation:', 'entry', 10)
        ])
        
        # Section Trading Scalping
        self.create_config_section(scrollable_frame, "🎯 TRADING SCALPING", [
            ('MAX_POSITION_SIZE', 'Taille max position:', 'float'),
            ('MAX_TOTAL_EXPOSURE', 'Exposition totale max:', 'float'),
            ('MAX_DAILY_LOSS', 'Perte journalière max:', 'float'),
            ('STOP_LOSS_PERCENT', 'Stop Loss (%):', 'float'),
            ('TAKE_PROFIT_PERCENT', 'Take Profit (%):', 'float'),
            ('RISK_REWARD_RATIO', 'Ratio Risque/Récompense:', 'float')
        ])
        
        # Section Filtrage des Paires
        self.create_config_section(scrollable_frame, "🔍 FILTRAGE DES PAIRES", [
            ('PAIR_SUFFIXES', 'Suffixes autorisés (séparés par virgule):', 'entry', 30),
            ('PAIR_SUFFIX_MODE', 'Mode de filtrage:', 'entry', 15)
        ])
        
        # Section Auto-scan
        self.create_config_section(scrollable_frame, "🔍 AUTO-SCAN TOUS LES ACTIFS", [
            ('AUTO_SCAN_ENABLED', 'Auto-scan activé:', 'bool'),
            ('SCAN_INTERVAL', 'Intervalle scan (s):', 'int'),
            ('SCAN_INTERVAL_MINUTES', 'Intervalle scan (minutes):', 'int'),
            ('SCAN_CONTINUOUS', 'Scan continu:', 'bool'),
            ('MAX_SCAN_RETRIES', 'Tentatives max:', 'int'),
            ('MAX_CRYPTOS', 'Cryptos maximum:', 'int')
        ])
        
        # Section Critères Volume optimisés
        self.create_config_section(scrollable_frame, "📊 CRITÈRES VOLUME OPTIMISÉS", [
            ('MIN_VOLUME_BTC_ETH', 'Volume min BTC/ETH:', 'int'),
            ('MIN_VOLUME_ALTCOINS', 'Volume min Altcoins:', 'int'),
            ('MIN_VOLUME_MICROCAPS', 'Volume min Microcaps:', 'int'),
            ('VOLUME_SPIKE_THRESHOLD', 'Seuil spike volume (%):', 'int')
        ])
        
        # Section Critères Pump optimisés
        self.create_config_section(scrollable_frame, "📈 CRITÈRES PUMP OPTIMISÉS", [
            ('MIN_PUMP_3MIN', 'Pump minimum 3min (%):', 'float'),
            ('MAX_PUMP_3MIN', 'Pump maximum 3min (%):', 'float')
        ])
        
        # Section RSI optimisé
        self.create_config_section(scrollable_frame, "📊 RSI OPTIMISÉ", [
            ('RSI_PERIOD', 'Période RSI:', 'int'),
            ('RSI_OVERSOLD', 'RSI Survente:', 'int'),
            ('RSI_OVERBOUGHT', 'RSI Surachat:', 'int'),
            ('RSI_CONFIRMATION_OVERSOLD', 'RSI Confirmation Survente:', 'int'),
            ('RSI_CONFIRMATION_OVERBOUGHT', 'RSI Confirmation Surachat:', 'int')
        ])
        
        # Section EMA
        self.create_config_section(scrollable_frame, "📈 CONFIGURATION EMA", [
            ('EMA_FAST', 'EMA rapide:', 'int'),
            ('EMA_SLOW', 'EMA lente:', 'int')
        ])
        
        # Section Filtres de Qualité Avancés
        self.create_config_section(scrollable_frame, "🎯 FILTRES DE QUALITÉ AVANCÉS", [
            ('MAX_SPREAD_PERCENT', 'Spread maximum (%):', 'float'),
            ('MIN_ORDER_BOOK_DEPTH', 'Profondeur carnet min:', 'int'),
            ('MIN_REQUIRED_SIGNALS', 'Signaux requis minimum:', 'int')
        ])
        
        # Section Capital Management Optimisé
        self.create_config_section(scrollable_frame, "💰 CAPITAL MANAGEMENT OPTIMISÉ", [
            ('INITIAL_BALANCE', 'Balance initiale:', 'float'),
            ('MAX_CRYPTOS', 'Cryptos maximum:', 'int'),
            ('POSITION_SIZE_USDT', 'Capital par crypto:', 'float')
        ])
        
        # Section Système de Sécurité à 3 Couches
        self.create_config_section(scrollable_frame, "🔒 SYSTÈME DE SÉCURITÉ À 3 COUCHES", [
            ('TRAILING_STOP_ENABLED', 'Trailing stop activé:', 'bool'),
            ('TRAILING_STOP_PERCENT', 'Trailing stop (%):', 'float'),
            ('TRAILING_ACTIVATION_PERCENT', 'Activation trailing (%):', 'float'),
            ('TIMEOUT_EXIT_SECONDS', 'Timeout sortie (s):', 'int'),
            ('STOP_LOSS_PERCENT', 'Stop loss (%):', 'float')
        ])
        
        # Section Trading Optimisé
        self.create_config_section(scrollable_frame, "💰 TRADING OPTIMISÉ", [
            ('TAKE_PROFIT_PERCENT', 'Take Profit (%):', 'float'),
            ('RISK_REWARD_RATIO', 'Ratio Risque/Récompense:', 'float')
        ])
        
        # Section Slippage Tracking
        self.create_config_section(scrollable_frame, "📊 SLIPPAGE TRACKING", [
            ('ENABLE_SLIPPAGE_TRACKING', 'Activer tracking slippage:', 'bool'),
            ('MAX_ACCEPTABLE_SLIPPAGE', 'Slippage max acceptable (%):', 'float')
        ])
        
        # Section Objectifs
        self.create_config_section(scrollable_frame, "🎯 OBJECTIFS", [
            ('DAILY_TARGET_PERCENT', 'Objectif journalier (%):', 'float'),
            ('MAX_TRADES_PER_DAY', 'Trades max par jour:', 'int'),
            ('MIN_SUCCESS_RATE', 'Taux succès min (%):', 'int')
        ])
        
        # Section Auto-start
        self.create_config_section(scrollable_frame, "🚀 DÉMARRAGE AUTOMATIQUE", [
            ('AUTO_START_BOT', 'Démarrer bot automatiquement:', 'bool')
        ])
        
        # Boutons de sauvegarde
        button_frame = tk.Frame(scrollable_frame, bg='#1a1a1a')
        button_frame.pack(fill='x', padx=20, pady=20)
        
        save_button = tk.Button(
            button_frame,
            text="💾 SAUVEGARDER CONFIGURATION",
            command=self.save_config,
            bg='#00aa44', fg='white',
            font=('Arial', 11, 'bold'),
            height=2
        )
        save_button.pack(side='left', padx=10)
        
        reset_button = tk.Button(
            button_frame,
            text="🔄 RESET DÉFAUT",
            command=self.reset_config,
            bg='#aa4400', fg='white',
            font=('Arial', 11, 'bold'),
            height=2
        )
        reset_button.pack(side='right', padx=10)
    
    def create_config_section(self, parent, title, fields):
        """Crée une section de configuration"""
        
        # Frame de la section
        section_frame = tk.Frame(parent, bg='#2d2d2d', relief='raised', bd=2)
        section_frame.pack(fill='x', padx=20, pady=10)
        
        # Titre
        tk.Label(section_frame, text=title, font=('Arial', 11, 'bold'), 
                fg='white', bg='#2d2d2d').pack(pady=10)
        
        # Champs
        for field_name, label_text, field_type, *args in fields:
            field_frame = tk.Frame(section_frame, bg='#2d2d2d')
            field_frame.pack(fill='x', padx=20, pady=3)
            
            # Label
            tk.Label(field_frame, text=label_text, fg='white', bg='#2d2d2d', 
                    font=('Arial', 9)).pack(side='left')
            
            # Champ selon le type
            if field_type == 'bool':
                var = tk.BooleanVar()
                widget = tk.Checkbutton(field_frame, variable=var, bg='#2d2d2d')
            elif field_type == 'entry':
                var = tk.StringVar()
                width = args[0] if args else 20
                widget = tk.Entry(field_frame, textvariable=var, width=width, bg='#3d3d3d', fg='white')
            else:  # int ou float
                var = tk.StringVar()
                widget = tk.Entry(field_frame, textvariable=var, width=15, bg='#3d3d3d', fg='white')
            
            widget.pack(side='right', padx=10)
            self.config_vars[field_name] = var
    
    def load_config_to_gui(self):
        """Charge la configuration dans l'interface"""
        for key, var_data in self.config_vars.items():
            value = self.config_manager.get(key, '')
            
            # Gérer les deux formats possibles
            if isinstance(var_data, tuple):
                var, param_type = var_data
                if param_type == "bool":
                    var.set(bool(value))
                else:
                    var.set(str(value))
            else:
                # Ancien format
                var = var_data
                if isinstance(var, tk.BooleanVar):
                    var.set(bool(value))
                else:
                    var.set(str(value))
    
    def save_config(self):
        """Sauvegarde la configuration et applique les changements"""
        try:
            # Vérification conforme
            new_config = {}
            for key, var_data in self.config_vars.items():
                # Gérer les deux formats possibles
                if isinstance(var_data, tuple):
                    var, param_type = var_data
                    value = var.get()
                else:
                    # Ancien format
                    var = var_data
                    value = var.get()
                
                # Conversion selon le type de paramètre
                if key in ['RSI_PERIOD', 'RSI_OVERSOLD', 'RSI_OVERBOUGHT', 'RSI_CONFIRMATION_OVERSOLD', 'RSI_CONFIRMATION_OVERBOUGHT',
                          'EMA_FAST', 'EMA_SLOW', 'MAX_CRYPTOS', 'SCAN_INTERVAL', 'SCAN_INTERVAL_MINUTES', 
                          'MAX_SCAN_RETRIES', 'MIN_VOLUME_BTC_ETH', 'MIN_VOLUME_ALTCOINS', 'MIN_VOLUME_MICROCAPS',
                          'VOLUME_SPIKE_THRESHOLD', 'MAX_TRADES_PER_DAY', 'MIN_SUCCESS_RATE', 'BINANCE_VIP_LEVEL',
                          'MIN_ORDER_BOOK_DEPTH', 'MIN_REQUIRED_SIGNALS', 'TIMEOUT_EXIT_SECONDS']:
                    new_config[key] = int(value) if value else 0
                elif key in ['MIN_PUMP_3MIN', 'MAX_PUMP_3MIN', 'MAX_POSITION_SIZE', 'MAX_TOTAL_EXPOSURE', 'MAX_DAILY_LOSS',
                            'TAKE_PROFIT_PERCENT', 'RISK_REWARD_RATIO', 'DAILY_TARGET_PERCENT',
                            'MAX_SPREAD_PERCENT', 'MAX_ACCEPTABLE_SLIPPAGE', 'INITIAL_BALANCE', 'POSITION_SIZE_USDT',
                            'TRAILING_STOP_PERCENT', 'TRAILING_ACTIVATION_PERCENT', 'STOP_LOSS_PERCENT']:
                    new_config[key] = float(value) if value else 0.0
                elif key in ['USE_BNB_DISCOUNT', 'AUTO_SCAN_ENABLED', 'SCAN_CONTINUOUS', 'TESTNET_MODE', 'SIMULATION_MODE', 
                            'AUTO_START_BOT', 'ENABLE_SLIPPAGE_TRACKING', 'TRAILING_STOP_ENABLED']:
                    new_config[key] = bool(value)
                else:
                    new_config[key] = value
            
            # Sauvegarder
            for key, value in new_config.items():
                self.config_manager.set(key, value)
            
            self.config_manager.save()
            
            # Appliquer les changements immédiatement si le bot est en cours d'exécution
            if self.bot_running and self.bot:
                self.apply_config_changes()
            
            messagebox.showinfo("Succès", "Configuration sauvegardée avec succès!\n\nLes nouveaux critères sont activés.")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur sauvegarde: {e}")
    
    def apply_config_changes(self):
        """Applique les changements de configuration au bot en cours d'exécution"""
        try:
            if not self.bot:
                return
            
            # Recharger la configuration dans le bot
            self.bot.config_manager = self.config_manager
            
            # Mettre à jour les paramètres critiques
            if hasattr(self.bot, 'scan_interval_minutes'):
                self.bot.scan_interval_minutes = self.config_manager.get('SCAN_INTERVAL_MINUTES', 1)
            
            # Mettre à jour les critères de scalping
            if hasattr(self.bot, 'scanner') and self.bot.scanner:
                self.bot.scanner.config_manager = self.config_manager
                self.bot.scanner.load_config()
            
            # Mettre à jour les critères de trading
            if hasattr(self.bot, 'max_cryptos'):
                self.bot.max_cryptos = self.config_manager.get('MAX_CRYPTOS', 5)
            
            self.on_log_message("⚙️ Configuration mise à jour en temps réel")
            
        except Exception as e:
            print(f"Erreur application config: {e}")
            self.on_log_message(f"⚠️ Erreur application config: {e}")
    
    def reset_config(self):
        """Reset la configuration par défaut"""
        if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir remettre la configuration par défaut?"):
            self.config_manager.create_default_config()
            self.load_config_to_gui()
            messagebox.showinfo("Succès", "Configuration remise par défaut!")
    
    def toggle_bot(self):
        """Démarre/arrête le bot"""
        if not self.bot_running:
            self.start_bot()
        else:
            self.stop_bot()
    
    def auto_start_bot(self):
        """Démarrage automatique du bot"""
        if not self.bot_running:
            self.on_log_message("🚀 Démarrage automatique du bot...")
            self.start_bot()
    
    def start_bot(self):
        """Démarre le bot"""
        try:
            # Pas de reload, utiliser directement la config
            self.bot = CryptoTradingBot(self.config_manager)
            
            # Callbacks pour GUI
            self.bot.add_callback('log_message', self.on_log_message)
            self.bot.add_callback('scan_update', self.on_scan_update)
            self.bot.add_callback('position_update', self.on_position_update)
            self.bot.add_callback('exchange_status', self.on_exchange_status)
            self.bot.add_callback('trade_executed', self.on_trade_executed)
            self.bot.add_callback('balance_update', self.on_balance_update)
            self.bot.add_callback('position_closed', self.on_position_closed)
            
            # Callback pour statut connexions
            def check_connections():
                import time
                while self.bot_running:
                    try:
                        # Vérifier si le bot a un exchange
                        exchange_connected = hasattr(self.bot, 'exchange') and self.bot.exchange is not None
                        
                        # Vérifier WebSocket
                        websocket_connected = (hasattr(self.bot, 'websocket_manager') and 
                                             self.bot.websocket_manager and 
                                             self.bot.websocket_manager.is_connected())
                        
                        # Mettre à jour l'interface
                        self.update_connection_status(websocket_connected, exchange_connected)
                        
                        time.sleep(5)  # Vérifier toutes les 5 secondes
                    except Exception as e:
                        print(f"Erreur check connexions: {e}")
                        time.sleep(5)
            
            threading.Thread(target=check_connections, daemon=True).start()
            
            # Démarrer dans un thread
            def start_thread():
                self.bot.start()
            
            threading.Thread(target=start_thread, daemon=True).start()
            
            # Charger l'état sauvegardé après démarrage
            self.root.after(2000, self.load_bot_state)  # Charger après 2 secondes
            
            self.bot_running = True
            self.control_button.config(text="🛑 ARRÊTER SCALPING", bg='#aa4400')
            self.status_label.config(text="🟢 BOT EN MARCHE", fg='#00aa44')
            
            # Adapter le bouton selon le mode
            if self.bot.simulation_mode:
                self.reset_button.config(text="🔄 RESET SIMULATION", bg='#ff6600')
            else:
                self.reset_button.config(text="💰 VENDRE POSITIONS", bg='#cc0000')
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur démarrage bot: {e}")
    
    def reset_simulation(self):
        """Reset de la simulation ou vente des positions selon le mode"""
        if not self.bot:
            return
            
        if self.bot.simulation_mode:
            # Mode simulation - Reset complet avec valeurs du config.txt
            initial_balance = float(self.bot.initial_balance)  # Conversion en nombre
            
            result = messagebox.askyesno(
                "Reset Simulation", 
                f"Êtes-vous sûr de vouloir :\n\n• Remettre la balance à {initial_balance:.2f}€\n• Fermer toutes les positions\n• Effacer l'historique\n\nCette action est irréversible !"
            )
            
            if result:
                # LOG avant reset
                positions_count = len(self.bot.open_positions) if self.bot.open_positions else 0
                self.bot.log(f"🔄 RESET SIMULATION: Fermeture de {positions_count} positions ouvertes")
                
                # Utiliser les valeurs du config.txt (conversion en nombres)
                self.bot.simulated_balance = float(initial_balance)
                self.bot.balance = float(initial_balance)
                
                # SUPPRIMER TOUS LES TRADES EN COURS
                self.bot.open_positions = []
                self.bot.total_trades = 0
                self.bot.winning_trades = 0
                self.bot.total_pnl = 0.0
                self.bot.total_fees = 0.0  # NOUVEAU: Remettre les frais à zéro
                
                # Nettoyer l'historique des trades fermés
                self.bot.closed_trades = []
                
                # ARRÊTER la surveillance des positions (important !)
                if hasattr(self.bot, 'position_monitor_active'):
                    self.bot.position_monitor_active = False
                
                # Sauvegarder immédiatement le reset
                self.bot.save_portfolio_state()
                
                # Nettoyer l'affichage des positions
                self.positions_text.delete(1.0, tk.END)
                self.positions_text.insert(1.0, "🔄 SIMULATION RÉINITIALISÉE\n\n✅ Toutes les positions ouvertes supprimées\n✅ Balance remise à {:.2f}€\n\n".format(float(initial_balance)))
                
                # Nettoyer l'historique des trades
                self.trades_history_text.config(state='normal')
                self.trades_history_text.delete(1.0, tk.END)
                self.trades_history_text.insert(1.0, "🔄 Historique réinitialisé - Aucun trade fermé\n")
                self.trades_history_text.config(state='disabled')
                
                # FORCER LE RAFRAÎCHISSEMENT COMPLET DE L'INTERFACE
                self.refresh_all_displays()
                
                # LOG confirmation
                self.bot.log("✅ RESET SIMULATION TERMINÉ - Toutes les positions supprimées")
                
                # Notifier le GUI que tout a changé
                self.on_log_message("✅ SIMULATION RÉINITIALISÉE - Toutes positions fermées")
                
                # Forcer la mise à jour de la balance
                if hasattr(self.bot, 'balance'):
                    self.on_balance_update(self.bot.balance, 0)  # 0 positions ouvertes
                
                # Notifier balance
                for callback in self.bot.callbacks.get('balance_update', []):
                    try:
                        callback(initial_balance, 0)
                    except Exception:
                        pass
                
                messagebox.showinfo("Succès", f"Simulation réinitialisée avec succès !\n\nBalance: {initial_balance}€\nPositions: 0\nHistorique: Effacé")
        else:
            # Mode réel - Demander vente des positions
            result = messagebox.askyesno(
                "Vendre Positions", 
                "⚠️ MODE RÉEL ⚠️\n\nVoulez-vous vendre TOUTES les positions ouvertes ?\n\nCette action va :\n• Fermer toutes les positions\n• Exécuter des ordres RÉELS\n• Affecter votre capital RÉEL\n\nÊtes-vous sûr ?"
            )
            
            if result:
                # Demander confirmation supplémentaire
                confirm = messagebox.askyesno(
                    "CONFIRMATION FINALE", 
                    "🚨 DERNIÈRE CHANCE 🚨\n\nVous êtes sur le point de vendre TOUTES vos positions RÉELLES.\n\nConfirmez-vous cette action ?"
                )
                
                if confirm:
                    self.sell_all_real_positions()
    
    def sell_all_real_positions(self):
        """Vend toutes les positions réelles"""
        try:
            if not self.bot or not self.bot.open_positions:
                messagebox.showinfo("Info", "Aucune position à vendre")
                return
            
            positions_to_close = [p for p in self.bot.open_positions if p['status'] == 'open']
            
            if not positions_to_close:
                messagebox.showinfo("Info", "Aucune position ouverte à vendre")
                return
                
            messagebox.showinfo("Vente en cours", f"Vente de {len(positions_to_close)} positions en cours...\n\nVeuillez patienter.")
            
            # Simuler vente des positions (à remplacer par vraie logique d'API)
            for position in positions_to_close:
                self.bot._close_position(position['symbol'], "Vente manuelle utilisateur")
                
            messagebox.showinfo("Succès", f"{len(positions_to_close)} positions vendues avec succès !")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la vente des positions:\n{e}")
    
    def save_bot_state(self):
        """Sauvegarde l'état du bot dans un fichier"""
        if not self.bot:
            return
            
        try:
            import json
            state = {
                'simulated_balance': self.bot.simulated_balance,
                'balance': self.bot.balance,
                'total_trades': self.bot.total_trades,
                'winning_trades': self.bot.winning_trades,
                'total_pnl': self.bot.total_pnl,
                'open_positions': [
                    {
                        **pos,
                        'timestamp': pos['timestamp'].isoformat() if hasattr(pos['timestamp'], 'isoformat') else str(pos['timestamp'])
                    } for pos in self.bot.open_positions
                ],
                'last_save': datetime.now().isoformat()
            }
            
            with open('bot_state.json', 'w') as f:
                json.dump(state, f, indent=2)
                
            self.log_text.insert(tk.END, f"💾 État sauvegardé: {len(self.bot.open_positions)} positions\n")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde état: {e}")
    
    def load_bot_state(self):
        """Charge l'état du bot depuis un fichier"""
        if not self.bot:
            return
            
        try:
            import json
            import os
            
            if not os.path.exists('bot_state.json'):
                return
                
            with open('bot_state.json', 'r') as f:
                state = json.load(f)
            
            # Restaurer l'état
            self.bot.simulated_balance = state.get('simulated_balance', 1000.0)
            self.bot.balance = state.get('balance', 1000.0)
            self.bot.total_trades = state.get('total_trades', 0)
            self.bot.winning_trades = state.get('winning_trades', 0)
            self.bot.total_pnl = state.get('total_pnl', 0.0)
            
            # Restaurer positions
            for pos_data in state.get('open_positions', []):
                pos_data['timestamp'] = datetime.fromisoformat(pos_data['timestamp'])
                self.bot.open_positions.append(pos_data)
            
            # Notifier balance
            for callback in self.bot.callbacks.get('balance_update', []):
                try:
                    callback(self.bot.balance, len(self.bot.open_positions))
                except Exception:
                    pass
            
            self.log_text.insert(tk.END, f"📂 État chargé: {len(self.bot.open_positions)} positions\n")
            
        except Exception as e:
            print(f"❌ Erreur chargement état: {e}")
    
    def stop_bot(self):
        """Arrête le bot"""
        # Sauvegarder l'état avant d'arrêter
        self.save_bot_state()
        
        if self.bot:
            self.bot.stop()
        
        self.bot_running = False
        self.control_button.config(text="🚀 DÉMARRER SCALPING", bg='#00aa44')
        self.status_label.config(text="📴 BOT ARRÊTÉ", fg='#ff4444')
        self.websocket_label.config(text="🔴 WEBSOCKET DÉCONNECTÉ", fg='#ff4444')
    
    def on_balance_update(self, balance, open_positions_count):
        """Callback pour mettre à jour la balance et stats - Thread-safe"""
        def update_gui():
            try:
                # CORRECTION: Logique simplifiée et correcte
                
                # 1. BALANCE DISPONIBLE = Cash libre pour trading
                available_balance = balance
                
                # 2. VALEUR DES POSITIONS OUVERTES (prix d'achat, pas prix actuel)
                positions_value = 0
                if hasattr(self.bot, 'open_positions') and self.bot.open_positions:
                    for position in self.bot.open_positions:
                        if position.get('status') == 'open':
                            positions_value += position.get('value_usdt', 0)
                
                # 3. VALEUR TOTALE = Balance disponible + Positions ouvertes
                total_portfolio_value = available_balance + positions_value
                
                # 4. P&L TOTAL = Somme des P&L réalisés + P&L des positions ouvertes
                
                # P&L réalisé des trades fermés
                realized_pnl = 0.0
                if hasattr(self.bot, 'closed_trades') and self.bot.closed_trades:
                    for trade in self.bot.closed_trades:
                        realized_pnl += trade.get('net_pnl', 0.0)
                
                # P&L non-réalisé des positions ouvertes
                unrealized_pnl = 0.0
                if hasattr(self.bot, 'open_positions') and self.bot.open_positions:
                    for position in self.bot.open_positions:
                        if position['status'] == 'open':
                            entry_price = position['price']
                            current_price = position.get('current_price', entry_price)
                            quantity = position['quantity']
                            unrealized_pnl += (current_price - entry_price) * quantity
                
                total_pnl = realized_pnl + unrealized_pnl
                
                # Calcul du pourcentage basé sur la balance initiale
                initial_balance = self.bot.config_manager.get('INITIAL_BALANCE', 1000.0)
                if isinstance(initial_balance, str):
                    initial_balance = float(initial_balance)
                
                pnl_percent = (total_pnl / initial_balance) * 100 if initial_balance > 0 else 0
                
                # Mettre à jour les labels
                self.balance_label.config(text=f"{available_balance:.2f} USDT")
                self.total_value_label.config(text=f"{total_portfolio_value:.2f} USDT")
                self.positions_count_label.config(text=f"{open_positions_count}")
                
                # P&L avec couleur correcte
                pnl_color = '#00ff88' if total_pnl >= 0 else '#ff4444'
                self.pnl_label.config(
                    text=f"{total_pnl:+.2f} USDT ({pnl_percent:+.1f}%)",
                    fg=pnl_color
                )
                
                # NOUVEAU: Frais totaux
                total_fees = getattr(self.bot, 'total_fees', 0.0)
                self.fees_label.config(text=f"-{total_fees:.2f} USDT")
                
                # Debug pour comprendre le calcul
                print(f"💰 DEBUG PORTFOLIO:")
                print(f"   Balance disponible: {available_balance:.2f} USDT")
                print(f"   Valeur positions: {positions_value:.2f} USDT")
                print(f"   Valeur totale: {total_portfolio_value:.2f} USDT")
                print(f"   Balance initiale: {initial_balance:.2f} USDT")
                print(f"   P&L total: {total_pnl:+.2f} USDT ({pnl_percent:+.1f}%)")
                print(f"   Frais totaux: -{total_fees:.2f} USDT")
                
                # Statistiques de trading
                if hasattr(self.bot, 'total_trades'):
                    self.trades_count_label.config(text=f"{self.bot.total_trades}")
                    
                    if self.bot.total_trades > 0:
                        win_rate = (self.bot.winning_trades / self.bot.total_trades) * 100
                        winrate_color = '#00ff88' if win_rate >= 60 else '#ff8800' if win_rate >= 40 else '#ff4444'
                        self.winrate_label.config(text=f"{win_rate:.1f}%", fg=winrate_color)
                
                # Mode de trading
                mode = "RÉEL" if not self.bot.simulation_mode else "SIMULATION"
                mode_color = '#ff4444' if mode == "RÉEL" else '#88aaff'
                self.mode_label.config(text=mode, fg=mode_color)
                
            except Exception as e:
                print(f"❌ Erreur mise à jour balance GUI: {e}")
        
        # Exécuter dans le thread principal
        self.root.after(0, update_gui)
    
    def on_position_closed(self, position):
        """Callback pour afficher les positions fermées - Thread-safe"""
        def update_gui():
            try:
                symbol = position['symbol']
                entry_price = position['price']
                exit_price = position['exit_price']
                pnl_usdt = position['pnl_usdt']
                pnl_percent = position['pnl_percent']
                timestamp = position['exit_timestamp'].strftime('%H:%M:%S')
                
                # Formatage prix
                if entry_price > 1:
                    entry_str = f"${entry_price:.4f}"
                    exit_str = f"${exit_price:.4f}"
                elif entry_price > 0.01:
                    entry_str = f"${entry_price:.6f}"
                    exit_str = f"${exit_price:.6f}"
                else:
                    entry_str = f"${entry_price:.10f}"
                    exit_str = f"${exit_price:.10f}"
                
                # Couleur selon profit/perte
                if pnl_usdt > 0:
                    color = '#00aa44'
                    emoji = '💰'
                else:
                    color = '#aa4400'
                    emoji = '📉'
                
                # Afficher la fermeture
                close_text = f"""[{timestamp}] {emoji} POSITION FERMÉE: {symbol}
   📈 Entrée: {entry_str} → 📊 Sortie: {exit_str}
   💵 P&L: ${pnl_usdt:+.2f} ({pnl_percent:+.2f}%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                
                # Ajouter en haut de la zone positions
                current_text = self.positions_text.get(1.0, tk.END)
                self.positions_text.delete(1.0, tk.END)
                self.positions_text.insert(1.0, close_text)
                self.positions_text.insert(tk.END, current_text)
                
                # Log aussi
                self.log_text.insert(tk.END, f"[{timestamp}] 💰 FERMÉ: {symbol} P&L: ${pnl_usdt:+.2f}\n")
                self.log_text.see(tk.END)
                
            except Exception as e:
                print(f"❌ Erreur affichage fermeture GUI: {e}")
        
        # Exécuter dans le thread principal
        self.root.after(0, update_gui)
    
    def on_trade_executed(self, trade_data):
        """Callback pour afficher les trades exécutés dans le GUI - Thread-safe"""
        def update_gui():
            try:
                symbol = trade_data['symbol']
                signal = trade_data['side']
                operation = trade_data['operation']  # ACHAT ou VENTE
                status = trade_data.get('status', 'open')
                price = trade_data['price']
                quantity = trade_data['quantity']
                value_usdt = trade_data['value_usdt']
                timestamp = trade_data['timestamp'].strftime('%H:%M:%S')
                order_id = trade_data['order_id']
                
                # Formatage adaptatif du prix pour PEPE, etc.
                if price > 1:
                    price_str = f"${price:.4f}"
                elif price > 0.01:
                    price_str = f"${price:.6f}"
                elif price > 0.0001:
                    price_str = f"${price:.8f}"
                else:
                    price_str = f"${price:.10f}"
                
                if status == 'closed':
                    # === POSITION FERMÉE (VENTE) ===
                    exit_price = trade_data.get('exit_price', price)
                    net_pnl = trade_data.get('net_pnl', 0)
                    pnl_percent = trade_data.get('pnl_percent', 0)
                    
                    # Formatage prix de sortie
                    if exit_price > 1:
                        exit_price_str = f"${exit_price:.4f}"
                    elif exit_price > 0.01:
                        exit_price_str = f"${exit_price:.6f}"
                    elif exit_price > 0.0001:
                        exit_price_str = f"${exit_price:.8f}"
                    else:
                        exit_price_str = f"${exit_price:.10f}"
                    
                    # Couleur selon P&L
                    if net_pnl > 0:
                        color = '#00aa44'
                        arrow = '✅'
                        pnl_color = '#00aa44'
                    else:
                        color = '#ff4444'
                        arrow = '❌'
                        pnl_color = '#ff4444'
                    
                    # Affichage vente + P&L
                    trade_text = f"""[{timestamp}] 💰 VENTE TERMINÉE: {symbol}
   {arrow} Entrée: {price_str} → Sortie: {exit_price_str}
   💸 P&L: {net_pnl:+.2f}€ ({pnl_percent:+.2f}%)
   🔄 Position fermée et effacée

"""
                    
                    # Ajouter à l'historique des trades fermés
                    self.add_closed_trade_to_history(trade_data)
                    
                    # Retirer cette position de l'affichage des positions ouvertes
                    self.remove_closed_position_from_gui(symbol)
                    
                else:
                    # === POSITION OUVERTE (ACHAT) ===
                    stop_loss = trade_data['stop_loss']
                    take_profit = trade_data.get('take_profit')  # NOUVEAU: Take Profit
                    change_24h = trade_data.get('change_24h', 0)
                    system_type = trade_data.get('system_type', 'LEGACY')
                    
                    # Formatage Stop Loss
                    if stop_loss > 1:
                        sl_str = f"${stop_loss:.4f}"
                    elif stop_loss > 0.01:
                        sl_str = f"${stop_loss:.6f}"
                    elif stop_loss > 0.0001:
                        sl_str = f"${stop_loss:.8f}"
                    else:
                        sl_str = f"${stop_loss:.10f}"
                    
                    # Formatage Take Profit (si disponible)
                    tp_str = ""
                    if take_profit:
                        if take_profit > 1:
                            tp_str = f"${take_profit:.4f}"
                        elif take_profit > 0.01:
                            tp_str = f"${take_profit:.6f}"
                        elif take_profit > 0.0001:
                            tp_str = f"${take_profit:.8f}"
                        else:
                            tp_str = f"${take_profit:.10f}"
                    
                    # Affichage simplifié : Toujours BUY maintenant
                    color = '#00aa44'  # Vert pour BUY
                    arrow = '📈'       # Flèche montante
                    
                    # Récupérer les infos du Take Profit dynamique
                    dynamic_tp_percent = trade_data.get('dynamic_tp_percent', 1.5)
                    
                    # Déterminer le niveau de potentiel pour l'affichage
                    if dynamic_tp_percent >= 3.0:
                        potential_level = "ÉLEVÉ 🔥"
                        potential_color = "#ff6600"
                    elif dynamic_tp_percent >= 2.0:
                        potential_level = "MOYEN 📈"
                        potential_color = "#ffaa00"
                    else:
                        potential_level = "STABLE 📊"
                        potential_color = "#00aaff"
                    
                    # Affichage selon le système
                    if system_type == 'SIMPLE_STOP_TAKE_PROFIT' and tp_str:
                        # NOUVEAU système avec Take Profit Dynamique
                        trade_text = f"""[{timestamp}] 🎮 POSITION OUVERTE: {symbol}
   {arrow} BUY {operation} | Potentiel: {potential_level} ({dynamic_tp_percent:.1f}%)
   💰 Prix: {price_str} | Quantité: {quantity:.8f}
   🛑 Stop Loss: {sl_str} | 🎯 Take Profit: {tp_str}
   💸 Valeur: {value_usdt:.2f}€ | Momentum: {change_24h:+.2f}%

"""
                    else:
                        # Ancien système : Afficher seulement Stop Loss (BUY uniquement)
                        trade_text = f"""[{timestamp}] 🎮 POSITION OUVERTE: {symbol}
   {arrow} BUY {operation} | Momentum: {change_24h:+.2f}%
   💰 Prix: {price_str} | Quantité: {quantity:.8f}
   🎯 Stop Loss: {sl_str}
   💸 Valeur: {value_usdt:.2f}€ | ID: {order_id}

"""
                
                # Ajouter le texte dans la zone positions
                self.positions_text.config(state='normal')
                self.positions_text.insert(tk.END, trade_text)
                self.positions_text.tag_add("trade_line", "end-2l", "end-1l")
                self.positions_text.tag_config("trade_line", foreground=color)
                self.positions_text.see(tk.END)
                self.positions_text.config(state='disabled')
                
            except Exception as e:
                print(f"❌ Erreur affichage trade GUI: {e}")
        
        # Exécuter dans le thread principal
        self.root.after(0, update_gui)
    
    def refresh_all_displays(self):
        """Rafraîchit complètement tous les affichages après un reset"""
        try:
            # Nettoyer complètement l'affichage des positions
            self.positions_text.config(state='normal')
            self.positions_text.delete(1.0, tk.END)
            
            # Si aucune position ouverte, afficher message de reset
            if not self.bot or not hasattr(self.bot, 'open_positions') or not self.bot.open_positions:
                self.positions_text.insert(1.0, "🔄 SIMULATION RÉINITIALISÉE\n\n✅ Aucune position ouverte\n✅ Balance remise à zéro\n\n")
            else:
                # S'il reste des positions (ne devrait pas arriver après reset), les afficher
                for position in self.bot.open_positions:
                    if position.get('status') == 'open':
                        # Réafficher la position
                        pass
                        
            self.positions_text.config(state='disabled')
            
            # Nettoyer aussi l'historique
            self.trades_history_text.config(state='normal') 
            self.trades_history_text.delete(1.0, tk.END)
            self.trades_history_text.insert(1.0, "🔄 Historique réinitialisé - Aucun trade fermé\n")
            self.trades_history_text.config(state='disabled')
            
            print("✅ Affichages rafraîchis après reset")
            
        except Exception as e:
            print(f"❌ Erreur rafraîchissement affichages: {e}")
    
    def remove_closed_position_from_gui(self, symbol):
        """Efface les positions fermées du GUI"""
        try:
            # Nettoyer l'affichage des positions ouvertes
            self.positions_text.config(state='normal')
            
            # Récupérer tout le texte
            current_text = self.positions_text.get(1.0, tk.END)
            lines = current_text.split('\n')
            
            # Filtrer les lignes - Supprimer TOUT le bloc de la position fermée
            filtered_lines = []
            skip_until_empty_line = False
            
            for line in lines:
                # Si on trouve une ligne avec ce symbole ET "TRADE OUVERT", commencer à skip
                if symbol in line and 'TRADE OUVERT' in line:
                    skip_until_empty_line = True
                    print(f"🗑️ Suppression position fermée: {symbol}")
                    continue
                
                # Si on est en mode skip, ignorer les lignes jusqu'à une ligne vide
                if skip_until_empty_line:
                    if line.strip() == '':  # Ligne vide = fin du bloc
                        skip_until_empty_line = False
                    continue
                
                # Garder toutes les autres lignes
                filtered_lines.append(line)
            
            # Réafficher le texte filtré
            self.positions_text.delete(1.0, tk.END)
            self.positions_text.insert(1.0, '\n'.join(filtered_lines))
            
            self.positions_text.config(state='disabled')
            print(f"✅ Position {symbol} supprimée de l'affichage")
            
        except Exception as e:
            print(f"❌ Erreur suppression position fermée: {e}")
    
    def on_exchange_status(self, status, details, testnet):
        """Callback pour le statut de connexion exchange - Thread-safe"""
        def update_gui():
            if status == 'connected':
                self.exchange_label.config(
                    text=f"📡 Binance: 🟢 CONNECTÉ ({details})",
                    fg='#00aa44'
                )
            elif status == 'auth_error':
                self.exchange_label.config(
                    text="📡 Binance: 🔴 ERREUR AUTH",
                    fg='#ff4444'
                )
            elif status == 'network_error':
                self.exchange_label.config(
                    text="📡 Binance: 🔴 ERREUR RÉSEAU",
                    fg='#ffaa00'
                )
            else:
                self.exchange_label.config(
                    text="📡 Binance: 🔴 DÉCONNECTÉ",
                    fg='#ff4444'
                )
        
        # Exécuter dans le thread principal
        self.root.after(0, update_gui)
    
    def on_log_message(self, message):
        """Callback pour les messages de log - Thread-safe"""
        def update_gui():
            self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
            self.log_text.see(tk.END)
            
            # Limiter les logs
            lines = self.log_text.get(1.0, tk.END).split('\n')
            if len(lines) > 100:
                self.log_text.delete(1.0, f"{len(lines)-100}.0")
        
        # Exécuter dans le thread principal
        self.root.after(0, update_gui)
    
    def on_scan_update(self, scan_stats, opportunities):
        """Callback pour mise à jour scan avec tous les détails - Thread-safe"""
        def update_gui():
            self.last_scan_stats = scan_stats
            self.last_opportunities = opportunities
            
            # Mettre à jour les compteurs détaillés comme l'ancien
            if hasattr(scan_stats, 'get'):
                total = scan_stats.get('total_tickers', 0)
                accepted = scan_stats.get('accepted_count', scan_stats.get('usdt_count', 0))
                filtered = scan_stats.get('filtered_count', 0)
                selected = scan_stats.get('opportunities_found', scan_stats.get('selected_count', 0))
                scan_time = scan_stats.get('scan_time', 0)
                
                self.scan_total_label.config(text=f"Total Binance: {total}")
                self.scan_usdt_label.config(text=f"Paires acceptées: {accepted}")
                self.scan_filtered_label.config(text=f"Après filtres: {filtered}")
                self.scan_selected_label.config(text=f"Sélectionnées: {selected}")
                self.last_scan_label.config(text=f"Dernier scan: {datetime.now().strftime('%H:%M:%S')} ({scan_time:.1f}s)")
            
            # Configuration des paires
            quote_currencies = self.config_manager.get('QUOTE_CURRENCIES', 'USDT BUSD BTC ETH BNB')
            
            # Critères de scan
            min_volume = self.config_manager.get('MIN_VOLUME_24H', 2000000) / 1_000_000
            min_pump = self.config_manager.get('MIN_PUMP_3MIN', 0.5)
            rsi_min = self.config_manager.get('RSI_MIN_SCALPING', 40)
            rsi_max = self.config_manager.get('RSI_MAX_SCALPING', 80)
            self.scan_criteria_label.config(text=f"Volume ≥{min_volume:.1f}M, Pump ≥{min_pump}%, RSI {rsi_min}-{rsi_max}")
            
            # Plus d'affichage des cryptos sélectionnées (remplacé par historique)
            pass
        
        # Exécuter dans le thread principal
        self.root.after(0, update_gui)
    
    def add_closed_trade_to_history(self, trade_data):
        """Ajoute un trade fermé à l'historique avec affichage détaillé sur 2 lignes"""
        try:
            # Extraction des données de base
            symbol = trade_data['symbol']
            entry_price = trade_data['price']
            exit_price = trade_data.get('exit_price', entry_price)
            net_pnl = trade_data.get('net_pnl', 0)
            pnl_percent = trade_data.get('pnl_percent', 0)
            total_fees = trade_data.get('total_fees', 0)
            
            # Gestion des timestamps (string ou datetime)
            timestamp = trade_data.get('timestamp', '')
            if isinstance(timestamp, str):
                try:
                    from datetime import datetime
                    timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp_str = timestamp_dt.strftime('%d/%m %H:%M:%S')
                except:
                    timestamp_str = timestamp[:16] if len(timestamp) > 16 else timestamp
            else:
                timestamp_str = timestamp.strftime('%d/%m %H:%M:%S') if timestamp else "N/A"
            
            # Calcul de la durée
            duration_str = "N/A"
            try:
                entry_time = trade_data.get('entry_time', trade_data.get('timestamp'))
                exit_time = trade_data.get('exit_time', trade_data.get('closed_at'))
                if entry_time and exit_time:
                    if isinstance(entry_time, str):
                        entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                    else:
                        entry_dt = entry_time
                    if isinstance(exit_time, str):
                        exit_dt = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
                    else:
                        exit_dt = exit_time
                    duration = exit_dt - entry_dt
                    minutes = int(duration.total_seconds() // 60)
                    seconds = int(duration.total_seconds() % 60)
                    duration_str = f"{minutes}m{seconds:02d}s"
            except Exception as e:
                duration_str = "N/A"
            
            # Ajouter à la liste
            self.closed_trades.append(trade_data)
            
            # Formatage des prix avec précision adaptative
            if entry_price > 1:
                entry_str = f"${entry_price:.4f}"
                exit_str = f"${exit_price:.4f}"
            elif entry_price > 0.01:
                entry_str = f"${entry_price:.6f}"
                exit_str = f"${exit_price:.6f}"
            elif entry_price > 0.0001:
                entry_str = f"${entry_price:.8f}"
                exit_str = f"${exit_price:.8f}"
            else:
                entry_str = f"${entry_price:.10f}"
                exit_str = f"${exit_price:.10f}"
            
            # Couleurs et icônes selon P&L
            if net_pnl > 0:
                main_color = '#00cc55'  # Vert vif pour les gains
                pnl_icon = '💚'
                perf_icon = '📈'
                tag_name = "profit"
            else:
                main_color = '#ff3366'  # Rouge vif pour les pertes
                pnl_icon = '💔'
                perf_icon = '📉'
                tag_name = "loss"
            
            # Données supplémentaires avec valeurs par défaut
            exit_reason = trade_data.get('exit_reason', 'N/A')
            momentum = trade_data.get('change_24h', 0)
            initial_tp = trade_data.get('take_profit', 0)
            dynamic_tp_percent = trade_data.get('dynamic_tp_percent', 0)
            
            # Formatage du momentum avec couleur
            if momentum > 0:
                momentum_str = f"+{momentum:.1f}%"
                momentum_icon = "🚀"
            elif momentum < 0:
                momentum_str = f"{momentum:.1f}%"
                momentum_icon = "📊"
            else:
                momentum_str = "0.0%"
                momentum_icon = "➖"
            
            # Formatage de la raison de fermeture avec emoji
            reason_icons = {
                'TAKE_PROFIT': '🎯',
                'STOP_LOSS': '🛑',
                'MOMENTUM': '📊',
                'TIMEOUT': '⏱️',
                'MANUAL': '👤',
                'TRAILING_STOP': '📈'
            }
            reason_icon = reason_icons.get(exit_reason, '❓')
            
            # LIGNE 1: Informations principales
            line1 = f"[{timestamp_str}] {pnl_icon} {symbol:<10} {entry_str} → {exit_str} {perf_icon} {net_pnl:+.2f}€ ({pnl_percent:+.1f}%) ⏱️{duration_str}\n"
            
            # LIGNE 2: Détails techniques (avec indentation pour clarté)
            tp_info = f"TP: {initial_tp:.4f}" if initial_tp > 0 else "TP: N/A"
            if dynamic_tp_percent > 0:
                tp_info += f"→{dynamic_tp_percent:.1f}%"
            
            line2 = f"    └─ {reason_icon} {exit_reason} • {momentum_icon} Momentum: {momentum_str} • 💰 Frais: {total_fees:.2f}€ • {tp_info}\n"
            
            # Combinaison des deux lignes
            trade_lines = line1 + line2
            
            # Insertion dans l'interface
            self.trades_history_text.config(state='normal')
            current_text = self.trades_history_text.get(1.0, tk.END)
            self.trades_history_text.delete(1.0, tk.END)
            
            # Si c'est le premier trade, supprimer le message d'attente
            if "Aucun trade fermé" in current_text:
                current_text = ""
            
            # Insérer les nouvelles lignes au début
            self.trades_history_text.insert(1.0, trade_lines)
            self.trades_history_text.insert(tk.END, current_text)
            
            # COLORATION AVANCÉE: Colorier les deux lignes avec nuances
            
            # Ligne 1 - Couleur principale pour P&L
            line1_start = "1.0"
            line1_end = "1.0 lineend"
            unique_tag_line1 = f"{tag_name}_main_{len(self.closed_trades)}"
            self.trades_history_text.tag_add(unique_tag_line1, line1_start, line1_end)
            self.trades_history_text.tag_config(unique_tag_line1, foreground=main_color, font=("Consolas", 9, "bold"))
            
            # Ligne 2 - Couleur plus claire pour les détails
            line2_start = "2.0"
            line2_end = "2.0 lineend"
            detail_color = '#009944' if net_pnl > 0 else '#cc2244'
            unique_tag_line2 = f"{tag_name}_detail_{len(self.closed_trades)}"
            self.trades_history_text.tag_add(unique_tag_line2, line2_start, line2_end)
            self.trades_history_text.tag_config(unique_tag_line2, foreground=detail_color, font=("Consolas", 8))
            
            # Configuration des tags génériques
            self.trades_history_text.tag_config("profit", foreground='#00cc55', font=("Consolas", 9, "bold"))
            self.trades_history_text.tag_config("loss", foreground='#ff3366', font=("Consolas", 9, "bold"))
            
            # Limiter à 25 trades max (50 lignes) pour performance
            lines = self.trades_history_text.get(1.0, tk.END).split('\n')
            if len(lines) > 50:  # 25 trades * 2 lignes
                truncated = '\n'.join(lines[:50])
                self.trades_history_text.delete(1.0, tk.END)
                self.trades_history_text.insert(1.0, truncated)
                
                # Réappliquer les couleurs après troncature
                self._reapply_trade_colors()
            
            self.trades_history_text.config(state='disabled')
            
            print(f"✅ Trade ajouté à l'historique: {symbol} P&L: {net_pnl:+.2f}€")
            
        except Exception as e:
            print(f"❌ Erreur ajout trade historique détaillé: {e}")
            import traceback
            traceback.print_exc()
    
    def _reapply_trade_colors(self):
        """Réapplique les couleurs à toutes les lignes de trades"""
        try:
            lines = self.trades_history_text.get(1.0, tk.END).split('\n')
            for i, line in enumerate(lines):
                if line.strip() and not "Aucun trade fermé" in line:
                    line_start = f"{i+1}.0"
                    line_end = f"{i+1}.0 lineend"
                    
                    # Déterminer la couleur selon le contenu
                    if "✅" in line:
                        color = '#00aa44'  # Vert pour profit
                    elif "❌" in line:
                        color = '#ff4444'  # Rouge pour perte
                    else:
                        continue
                    
                    # Appliquer la couleur
                    tag_name = f"line_{i}"
                    self.trades_history_text.tag_add(tag_name, line_start, line_end)
                    self.trades_history_text.tag_config(tag_name, foreground=color)
                    
        except Exception as e:
            print(f"❌ Erreur réapplication couleurs: {e}")
    
    def update_performance(self, balance: float, pnl: float, trades_count: int, win_rate: float, positions_count: int):
        """Met à jour les statistiques de performance comme l'ancien GUI"""
        self.balance_label.config(text=f"Balance: {balance:.2f} USDT")
        
        pnl_text = f"P&L: {pnl:+.2f} USDT ({(pnl/balance*100):+.1f}%)" if balance > 0 else f"P&L: {pnl:+.2f} USDT"
        pnl_color = '#00ff88' if pnl >= 0 else '#ff4444'
        self.pnl_label.config(text=pnl_text, fg=pnl_color)
        
        self.trades_label.config(text=f"Trades: {trades_count} (Win: {win_rate:.1f}%)")
        self.positions_count_label.config(text=f"Positions: {positions_count} ouvertes")
    
    def update_connection_status(self, websocket_connected: bool, exchange_connected: bool):
        """Met à jour le statut des connexions - Thread-safe"""
        def update_gui():
            ws_text = "🟢 CONNECTÉ" if websocket_connected else "🔴 DÉCONNECTÉ"
            ws_color = '#00ff88' if websocket_connected else '#ff4444'
            self.websocket_label.config(text=f"⚡ WebSocket: {ws_text}", fg=ws_color)
            
            ex_text = "🟢 CONNECTÉ" if exchange_connected else "🔴 DÉCONNECTÉ"
            ex_color = '#00ff88' if exchange_connected else '#ff4444'
            self.exchange_label.config(text=f"📡 Binance: {ex_text}", fg=ex_color)
        
        # Exécuter dans le thread principal
        self.root.after(0, update_gui)
    
    def on_position_update(self, action, symbol, position_data):
        """Callback pour mise à jour positions - Thread-safe"""
        def update_gui():
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if action == 'open':
                direction = position_data.get('direction', 'N/A')
                price = position_data.get('entry_price', 0)
                # Formatage adaptatif du prix
                if price > 1:
                    price_str = f"${price:.4f}"
                elif price > 0.01:
                    price_str = f"${price:.6f}" 
                elif price > 0.0001:
                    price_str = f"${price:.8f}"
                else:
                    price_str = f"${price:.10f}"
                    
                self.positions_text.insert(tk.END, f"[{timestamp}] 🟢 OUVERT: {symbol} {direction.upper()} @ {price_str}\n")
            elif action == 'close':
                pnl = position_data.get('pnl', 0)
                color = "🟢" if pnl > 0 else "🔴"
                self.positions_text.insert(tk.END, f"[{timestamp}] {color} FERMÉ: {symbol} - P&L: {pnl:+.2f} USDT\n")
            
            self.positions_text.see(tk.END)
        
        # Exécuter dans le thread principal
        self.root.after(0, update_gui)
    
    def create_config_tab(self):
        """SUPPRIMÉ - Configuration redondante"""
        pass
    
    def create_config_section_old(self, parent, title, params):
        """SUPPRIMÉ - Méthode redondante"""
        pass
    
    def save_config_old(self):
        """SUPPRIMÉ - Méthode redondante"""
        pass
    
    def load_current_config(self):
        """SUPPRIMÉ - Méthode redondante"""
        pass
    
    def load_default_config(self):
        """SUPPRIMÉ - Méthode redondante"""
        pass
    
    def test_connection(self):
        """SUPPRIMÉ - Méthode redondante"""
        pass

    def run(self):
        """Lance l'interface"""
        self.root.mainloop()

def main():
    """Fonction principale"""
    app = ScalpingBotGUI()
    app.run()

if __name__ == "__main__":
    main()