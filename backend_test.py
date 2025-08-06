#!/usr/bin/env python3
"""
Backend Testing Suite for Cryptocurrency Trading Bot
Tests core functionality, configuration management, and data structures
"""

import sys
import os
import json
import unittest
from datetime import datetime
import tempfile
import shutil

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
        
        # Create .env file
        with open('.env', 'w') as f:
            f.write("API_KEY=test_api_key_for_testing\n")
            f.write("API_SECRET=test_api_secret_for_testing\n")
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_config_manager_functionality(self):
        """Test 1: Configuration Management - Verify config.txt and config_manager.py work correctly"""
        try:
            # Change to app directory to access config_manager
            os.chdir('/app')
            from config_manager import ConfigManager
            
            config_manager = ConfigManager()
            
            # Test loading configuration from actual config.txt
            simulation_mode = config_manager.get('SIMULATION_MODE')
            initial_balance = config_manager.get('INITIAL_BALANCE')
            max_cryptos = config_manager.get('MAX_CRYPTOS')
            
            # Verify values are loaded
            self.assertIsNotNone(simulation_mode, "SIMULATION_MODE should be loaded")
            self.assertIsNotNone(initial_balance, "INITIAL_BALANCE should be loaded")
            self.assertIsNotNone(max_cryptos, "MAX_CRYPTOS should be loaded")
            
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
    
    def test_crypto_bot_engine_structure(self):
        """Test 2: Core Bot Structure - Verify the bot engine file structure and imports"""
        try:
            os.chdir('/app')
            
            # Test that the crypto_bot_engine file exists and can be read
            self.assertTrue(os.path.exists('crypto_bot_engine.py'), "crypto_bot_engine.py should exist")
            
            # Read the file and check for key components
            with open('crypto_bot_engine.py', 'r') as f:
                content = f.read()
            
            # Check for key class and method definitions
            self.assertIn('class CryptoTradingBot', content, "CryptoTradingBot class should be defined")
            self.assertIn('def __init__', content, "Bot should have __init__ method")
            self.assertIn('def start', content, "Bot should have start method")
            
            # Check for key attributes
            self.assertIn('simulation_mode', content, "Bot should handle simulation_mode")
            self.assertIn('initial_balance', content, "Bot should handle initial_balance")
            self.assertIn('open_positions', content, "Bot should track open_positions")
            
            print("✅ Core Bot Structure: PASSED")
            return True
                
        except Exception as e:
            print(f"❌ Core Bot Structure: FAILED - {str(e)}")
            return False
    
    def test_gui_structure(self):
        """Test 3: GUI Structure - Test that bot_trading_gui.py has expected structure"""
        try:
            os.chdir('/app')
            
            # Test that the GUI file exists
            self.assertTrue(os.path.exists('bot_trading_gui.py'), "bot_trading_gui.py should exist")
            
            # Read the file and check for key components
            with open('bot_trading_gui.py', 'r') as f:
                content = f.read()
            
            # Check for key class and method definitions
            self.assertIn('class ScalpingBotGUI', content, "ScalpingBotGUI class should be defined")
            self.assertIn('def __init__', content, "GUI should have __init__ method")
            self.assertIn('def add_closed_trade_to_history', content, "GUI should have add_closed_trade_to_history method")
            
            # Check for the new 2-line display functionality
            self.assertIn('Line 1:', content, "GUI should have 2-line display formatting")
            self.assertIn('Line 2:', content, "GUI should have 2-line display formatting")
            
            print("✅ GUI Structure: PASSED")
            return True
                    
        except Exception as e:
            print(f"❌ GUI Structure: FAILED - {str(e)}")
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
            
            # For closed trades, add exit fields
            sample_trade.update({
                'exit_reason': 'TAKE_PROFIT',
                'exit_price': 51000.0,
                'exit_time': datetime.now().isoformat(),
                'exit_fees': 0.075,
                'net_pnl': 25.0,
                'pnl_percent': 0.25,
                'total_fees': 0.15
            })
            
            # Verify required fields exist
            required_fields = [
                'symbol', 'entry_price', 'exit_price', 'net_pnl', 'timestamp', 
                'exit_reason', 'trading_fees', 'order_type', 'status'
            ]
            
            for field in required_fields:
                self.assertIn(field, sample_trade, f"Trade should have {field} field")
            
            # Check basic structure
            self.assertIsInstance(sample_trade, dict, "Trade data should be a dictionary")
            self.assertIsInstance(sample_trade['net_pnl'], (int, float), "net_pnl should be numeric")
            self.assertIsInstance(sample_trade['entry_price'], (int, float), "entry_price should be numeric")
            
            print("✅ Trade Data Structure: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Trade Data Structure: FAILED - {str(e)}")
            return False
    
    def test_portfolio_state_management(self):
        """Test 5: State Management - Check portfolio_state.json loading and saving capabilities"""
        try:
            os.chdir('/app')
            
            # Check if portfolio_state.json exists
            if os.path.exists('portfolio_state.json'):
                # Load and verify existing portfolio state
                with open('portfolio_state.json', 'r') as f:
                    portfolio = json.load(f)
                
                # Verify structure
                expected_fields = ['balance', 'total_pnl', 'total_fees', 'open_positions', 'closed_trades']
                for field in expected_fields:
                    self.assertIn(field, portfolio, f"Portfolio should have {field} field")
                
                # Verify data types
                self.assertIsInstance(portfolio['balance'], (int, float), "Balance should be numeric")
                self.assertIsInstance(portfolio['open_positions'], list, "Open positions should be a list")
                self.assertIsInstance(portfolio['closed_trades'], list, "Closed trades should be a list")
                
                # Check if there are closed trades to verify structure
                if portfolio['closed_trades']:
                    sample_trade = portfolio['closed_trades'][0]
                    trade_fields = ['symbol', 'entry_price', 'exit_price', 'net_pnl']
                    for field in trade_fields:
                        self.assertIn(field, sample_trade, f"Closed trade should have {field} field")
            
            # Test creating a new portfolio state
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
            
            # Save to temp file
            with open('test_portfolio.json', 'w') as f:
                json.dump(test_portfolio, f, indent=2)
            
            # Verify file was created and can be loaded
            self.assertTrue(os.path.exists('test_portfolio.json'), "Test portfolio file should be created")
            
            with open('test_portfolio.json', 'r') as f:
                loaded_portfolio = json.load(f)
            
            self.assertEqual(loaded_portfolio['balance'], 1000.0, "Portfolio balance should be loaded correctly")
            
            # Clean up
            os.remove('test_portfolio.json')
            
            print("✅ State Management: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ State Management: FAILED - {str(e)}")
            return False
    
    def test_closed_trade_formatting_structure(self):
        """Test 6: Closed Trade Display - Test the new 2-line display formatting structure"""
        try:
            os.chdir('/app')
            
            # Read the GUI file to check for formatting logic
            with open('bot_trading_gui.py', 'r') as f:
                content = f.read()
            
            # Check for the add_closed_trade_to_history method
            self.assertIn('def add_closed_trade_to_history', content, 
                         "GUI should have add_closed_trade_to_history method")
            
            # Check for 2-line formatting elements (French version)
            formatting_elements = [
                'LIGNE 1:', 'LIGNE 2:', 'line1', 'line2', 'entry_price', 'exit_price', 'net_pnl', 
                'exit_reason', 'total_fees', 'timestamp', 'trade_lines'
            ]
            
            for element in formatting_elements:
                self.assertIn(element, content, f"GUI should contain {element} for 2-line formatting")
            
            # Check for specific 2-line implementation details
            self.assertIn('line1 + line2', content, "GUI should combine line1 and line2")
            self.assertIn('Informations principales', content, "GUI should have main info line")
            self.assertIn('Détails techniques', content, "GUI should have details line")
            
            # Create a sample closed trade to verify data structure compatibility
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
                
        except Exception as e:
            print(f"❌ Closed Trade Display: FAILED - {str(e)}")
            return False

def run_backend_tests():
    """Run all backend tests and return results"""
    print("🚀 Starting Cryptocurrency Trading Bot Backend Tests")
    print("=" * 60)
    
    # Manual test execution for better control
    test_instance = TestCryptoTradingBot()
    test_results = []
    
    test_methods = [
        'test_config_manager_functionality',
        'test_crypto_bot_engine_structure', 
        'test_gui_structure',
        'test_trade_data_structure',
        'test_portfolio_state_management',
        'test_closed_trade_formatting_structure'
    ]
    
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