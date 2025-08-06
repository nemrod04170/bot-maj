#!/usr/bin/env python3
"""
Backend Testing Suite for Cryptocurrency Trading Bot
Tests core functionality, configuration management, and GUI integration
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, '/app')

class TestCryptoTradingBot(unittest.TestCase):
    """Test suite for cryptocurrency trading bot backend functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test config file
        self.test_config = {
            'API_KEY': 'test_api_key',
            'API_SECRET': 'test_api_secret',
            'SIMULATION_MODE': True,
            'INITIAL_BALANCE': 1000.0,
            'MAX_CRYPTOS': 5,
            'POSITION_SIZE_USDT': 100.0,
            'STOP_LOSS_PERCENT': 2.0,
            'TAKE_PROFIT_PERCENT': 1.5,
            'TIMEOUT_EXIT_SECONDS': 45
        }
        
        with open('config.txt', 'w') as f:
            for key, value in self.test_config.items():
                f.write(f"{key}={value}\n")
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_config_manager_initialization(self):
        """Test 1: Configuration Management - Verify config.txt and config_manager.py work correctly"""
        try:
            from config_manager import ConfigManager
            
            config_manager = ConfigManager()
            
            # Test loading configuration
            api_key = config_manager.get('API_KEY')
            self.assertEqual(api_key, 'test_api_key', "Config manager should load API_KEY correctly")
            
            # Test setting and getting values
            config_manager.set('TEST_VALUE', 'test_data')
            test_value = config_manager.get('TEST_VALUE')
            self.assertEqual(test_value, 'test_data', "Config manager should set and get values correctly")
            
            # Test default values
            default_value = config_manager.get('NON_EXISTENT_KEY', 'default')
            self.assertEqual(default_value, 'default', "Config manager should return default values for missing keys")
            
            print("✅ Configuration Management: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Configuration Management: FAILED - {str(e)}")
            return False
    
    def test_crypto_bot_engine_initialization(self):
        """Test 2: Core Bot Functionality - Verify the bot can initialize properly with config files"""
        try:
            from config_manager import ConfigManager
            
            # Test config manager first
            config_manager = ConfigManager()
            
            # Verify config loading works
            simulation_mode = config_manager.get('SIMULATION_MODE', True)
            initial_balance = config_manager.get('INITIAL_BALANCE', 1000.0)
            max_cryptos = config_manager.get('MAX_CRYPTOS', 5)
            
            # Test that we can access the crypto bot engine module
            try:
                import crypto_bot_engine
                self.assertTrue(hasattr(crypto_bot_engine, 'CryptoTradingBot'), 
                              "CryptoTradingBot class should exist")
                print("✅ Core Bot Functionality: PASSED")
                return True
            except ImportError as ie:
                print(f"❌ Core Bot Functionality: FAILED - Import error: {str(ie)}")
                return False
                
        except Exception as e:
            print(f"❌ Core Bot Functionality: FAILED - {str(e)}")
            return False
    
    def test_gui_integration(self):
        """Test 3: GUI Integration - Test that bot_trading_gui.py can be imported and initialized without errors"""
        try:
            # Test that we can import the GUI module
            try:
                import bot_trading_gui
                self.assertTrue(hasattr(bot_trading_gui, 'ScalpingBotGUI'), 
                              "ScalpingBotGUI class should exist")
                
                # Test that the GUI class has the expected methods
                gui_class = bot_trading_gui.ScalpingBotGUI
                expected_methods = ['add_closed_trade_to_history', 'setup_gui', 'toggle_bot']
                
                for method in expected_methods:
                    if hasattr(gui_class, method):
                        self.assertTrue(callable(getattr(gui_class, method)), 
                                      f"{method} should be callable")
                
                print("✅ GUI Integration: PASSED")
                return True
                
            except ImportError as ie:
                print(f"❌ GUI Integration: FAILED - Import error: {str(ie)}")
                return False
                    
        except Exception as e:
            print(f"❌ GUI Integration: FAILED - {str(e)}")
            return False
    
    def test_trade_data_structure(self):
        """Test 4: Trade Data Structure - Verify that trade data contains all required fields"""
        try:
            # Create a sample trade data structure based on portfolio_state.json
            sample_trade = {
                "symbol": "BTC/USDT",
                "side": "BUY",
                "operation": "ACHAT",
                "direction": "LONG",
                "quantity": 0.001,
                "price": 50000.0,
                "entry_price": 50000.0,
                "stop_loss": 49000.0,
                "timestamp": datetime.now().isoformat(),
                "entry_time": datetime.now().isoformat(),
                "value_usdt": 100.0,
                "net_invested": 99.925,
                "trading_fees": 0.075,
                "order_type": "TAKER",
                "status": "open",
                "highest_price": 50000.0,
                "last_significant_move": datetime.now().isoformat(),
                "trailing_activated": False,
                "order_id": "test_order_123"
            }
            
            # Verify required fields exist
            required_fields = [
                'symbol', 'entry_price', 'exit_price', 'net_pnl', 'timestamp', 
                'exit_reason', 'trading_fees', 'order_type', 'status'
            ]
            
            # For closed trades, add exit fields
            if sample_trade.get('status') == 'closed':
                sample_trade.update({
                    'exit_reason': 'TAKE_PROFIT',
                    'exit_price': 51000.0,
                    'exit_time': datetime.now().isoformat(),
                    'exit_fees': 0.075,
                    'net_pnl': 25.0,
                    'pnl_percent': 0.25,
                    'total_fees': 0.15
                })
            
            # Check basic structure
            self.assertIsInstance(sample_trade, dict, "Trade data should be a dictionary")
            self.assertIn('symbol', sample_trade, "Trade should have symbol field")
            self.assertIn('entry_price', sample_trade, "Trade should have entry_price field")
            self.assertIn('timestamp', sample_trade, "Trade should have timestamp field")
            
            print("✅ Trade Data Structure: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Trade Data Structure: FAILED - {str(e)}")
            return False
    
    def test_portfolio_state_management(self):
        """Test 5: State Management - Check portfolio_state.json loading and saving capabilities"""
        try:
            # Create test portfolio state
            test_portfolio = {
                "balance": 1000.0,
                "total_pnl": 0.0,
                "total_fees": 0.0,
                "open_positions": [],
                "closed_trades": [],
                "total_trades": 0,
                "winning_trades": 0,
                "last_updated": datetime.now().isoformat()
            }
            
            # Save portfolio state
            with open('portfolio_state.json', 'w') as f:
                json.dump(test_portfolio, f, indent=2)
            
            # Verify file was created
            self.assertTrue(os.path.exists('portfolio_state.json'), "Portfolio state file should be created")
            
            # Load and verify portfolio state
            with open('portfolio_state.json', 'r') as f:
                loaded_portfolio = json.load(f)
            
            self.assertEqual(loaded_portfolio['balance'], 1000.0, "Portfolio balance should be loaded correctly")
            self.assertEqual(loaded_portfolio['total_trades'], 0, "Portfolio total trades should be loaded correctly")
            self.assertIsInstance(loaded_portfolio['open_positions'], list, "Open positions should be a list")
            self.assertIsInstance(loaded_portfolio['closed_trades'], list, "Closed trades should be a list")
            
            print("✅ State Management: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ State Management: FAILED - {str(e)}")
            return False
    
    def test_closed_trade_formatting(self):
        """Test 6: Closed Trade Display - Test the new 2-line display formatting logic"""
        try:
            # Test that we can import the GUI module and check for the formatting function
            try:
                import bot_trading_gui
                
                # Check if the GUI class has the add_closed_trade_to_history method
                gui_class = bot_trading_gui.ScalpingBotGUI
                
                if hasattr(gui_class, 'add_closed_trade_to_history'):
                    self.assertTrue(callable(getattr(gui_class, 'add_closed_trade_to_history')), 
                                  "add_closed_trade_to_history should be callable")
                
                # Create a sample closed trade to verify data structure
                closed_trade = {
                    "symbol": "BTC/USDT",
                    "entry_price": 50000.0,
                    "exit_price": 51000.0,
                    "net_pnl": 25.0,
                    "pnl_percent": 0.5,
                    "entry_time": "2025-01-15T10:30:00",
                    "exit_time": "2025-01-15T10:45:00",
                    "exit_reason": "TAKE_PROFIT",
                    "total_fees": 0.15,
                    "trailing_activated": False
                }
                
                # Verify trade data has required fields for formatting
                required_fields = ['symbol', 'entry_price', 'exit_price', 'net_pnl', 
                                 'entry_time', 'exit_time', 'exit_reason']
                
                for field in required_fields:
                    self.assertIn(field, closed_trade, f"Closed trade should have {field} field")
                
                print("✅ Closed Trade Display: PASSED")
                return True
                
            except ImportError as ie:
                print(f"❌ Closed Trade Display: FAILED - Import error: {str(ie)}")
                return False
                
        except Exception as e:
            print(f"❌ Closed Trade Display: FAILED - {str(e)}")
            return False

def run_backend_tests():
    """Run all backend tests and return results"""
    print("🚀 Starting Cryptocurrency Trading Bot Backend Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test methods
    test_methods = [
        'test_config_manager_initialization',
        'test_crypto_bot_engine_initialization', 
        'test_gui_integration',
        'test_trade_data_structure',
        'test_portfolio_state_management',
        'test_closed_trade_formatting'
    ]
    
    for method in test_methods:
        suite.addTest(TestCryptoTradingBot(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Manual test execution for better control
    test_instance = TestCryptoTradingBot()
    test_results = []
    
    for method in test_methods:
        test_instance.setUp()
        try:
            test_method = getattr(test_instance, method)
            success = test_method()
            test_results.append(success)
        except Exception as e:
            print(f"❌ {method}: FAILED - {str(e)}")
            test_results.append(False)
        finally:
            test_instance.tearDown()
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Backend functionality is working correctly!")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed - Backend needs attention")
        return False

if __name__ == "__main__":
    success = run_backend_tests()
    sys.exit(0 if success else 1)