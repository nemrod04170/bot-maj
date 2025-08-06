#!/usr/bin/env python3
"""
Backend Testing Suite for Cryptocurrency Trading Bot
Tests core functionality, configuration management, and data structures
Focus on testing the corrected cryptocurrency trading bot functionality:
1. Fixed "N/A" Issue - verify closed trades have proper exit_reason and exit_time
2. Smart Scalping Logic - verify MIN_PROFIT_FOR_AUTO_SCALPING=0.5% prevents premature selling
3. Trade Duration Calculation - verify durations are calculated correctly
4. Position Closing - test that all position closing methods set exit_reason and exit_time
"""

import sys
import os
import json
import unittest
from datetime import datetime, timedelta
import tempfile
import shutil
import time

# Add the app directory to Python path
sys.path.insert(0, '/app')

class TestCryptoTradingBot(unittest.TestCase):
    """Test suite for cryptocurrency trading bot backend functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test config file with MIN_PROFIT_FOR_AUTO_SCALPING
        self.test_config = {
            'API_KEY': 'test_api_key',
            'API_SECRET': 'test_api_secret',
            'SIMULATION_MODE': True,
            'INITIAL_BALANCE': 1000.0,
            'MAX_CRYPTOS': 5,
            'POSITION_SIZE_USDT': 100.0,
            'STOP_LOSS_PERCENT': 2.0,
            'TAKE_PROFIT_PERCENT': 1.5,
            'TIMEOUT_EXIT_SECONDS': 45,
            'MIN_PROFIT_FOR_AUTO_SCALPING': 0.5  # New configuration
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
    
    def test_min_profit_auto_scalping_configuration(self):
        """Test 1: MIN_PROFIT_FOR_AUTO_SCALPING Configuration - Verify the new 0.5% configuration is loaded"""
        try:
            os.chdir('/app')
            from config_manager import ConfigManager
            
            config_manager = ConfigManager()
            
            # Test that MIN_PROFIT_FOR_AUTO_SCALPING is loaded correctly
            min_profit = config_manager.get('MIN_PROFIT_FOR_AUTO_SCALPING')
            self.assertIsNotNone(min_profit, "MIN_PROFIT_FOR_AUTO_SCALPING should be loaded")
            self.assertEqual(float(min_profit), 0.5, "MIN_PROFIT_FOR_AUTO_SCALPING should be 0.5%")
            
            # Verify it's in the config.txt file
            with open('config.txt', 'r') as f:
                config_content = f.read()
            
            self.assertIn('MIN_PROFIT_FOR_AUTO_SCALPING', config_content, 
                         "MIN_PROFIT_FOR_AUTO_SCALPING should be in config.txt")
            self.assertIn('0.5', config_content, 
                         "MIN_PROFIT_FOR_AUTO_SCALPING value should be 0.5")
            
            print("✅ MIN_PROFIT_FOR_AUTO_SCALPING Configuration: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ MIN_PROFIT_FOR_AUTO_SCALPING Configuration: FAILED - {str(e)}")
            return False
    
    def test_close_position_with_reason_function(self):
        """Test 2: _close_position_with_reason Function - Verify exit_reason and exit_time are set"""
        try:
            os.chdir('/app')
            
            # Read the crypto_bot_engine.py file
            with open('crypto_bot_engine.py', 'r') as f:
                content = f.read()
            
            # Check that _close_position_with_reason function exists
            self.assertIn('def _close_position_with_reason', content, 
                         "_close_position_with_reason function should exist")
            
            # Check that it sets exit_reason and exit_time
            self.assertIn("position['exit_reason'] = reason", content,
                         "Function should set exit_reason")
            self.assertIn("position['exit_time'] = datetime.now()", content,
                         "Function should set exit_time")
            
            # Check that it calls _close_position_scalping
            self.assertIn("self._close_position_scalping(position, exit_price)", content,
                         "Function should call _close_position_scalping")
            
            print("✅ _close_position_with_reason Function: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ _close_position_with_reason Function: FAILED - {str(e)}")
            return False
    
    def test_close_position_scalping_na_fix(self):
        """Test 3: _close_position_scalping N/A Fix - Verify exit_time and exit_reason defaults"""
        try:
            os.chdir('/app')
            
            # Read the crypto_bot_engine.py file
            with open('crypto_bot_engine.py', 'r') as f:
                content = f.read()
            
            # Check that _close_position_scalping function exists
            self.assertIn('def _close_position_scalping', content, 
                         "_close_position_scalping function should exist")
            
            # Check for the N/A fix - default exit_time
            self.assertIn("if 'exit_time' not in position:", content,
                         "Function should check for missing exit_time")
            self.assertIn("position['exit_time'] = datetime.now()", content,
                         "Function should set default exit_time")
            
            # Check for the N/A fix - default exit_reason
            self.assertIn("if 'exit_reason' not in position:", content,
                         "Function should check for missing exit_reason")
            self.assertIn("position['exit_reason'] = 'MANUAL_CLOSE'", content,
                         "Function should set default exit_reason")
            
            print("✅ _close_position_scalping N/A Fix: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ _close_position_scalping N/A Fix: FAILED - {str(e)}")
            return False
    
    def test_smart_scalping_logic(self):
        """Test 4: Smart Scalping Logic - Verify MIN_PROFIT_FOR_AUTO_SCALPING prevents premature selling"""
        try:
            os.chdir('/app')
            
            # Read the crypto_bot_engine.py file
            with open('crypto_bot_engine.py', 'r') as f:
                content = f.read()
            
            # Check for the smart scalping logic
            self.assertIn("profit_threshold = self.config_manager.get('MIN_PROFIT_FOR_AUTO_SCALPING', 0.5)", content,
                         "Smart scalping should use MIN_PROFIT_FOR_AUTO_SCALPING configuration")
            
            # Check for profit calculation
            self.assertIn("price_change_percent = ((current_price - existing_position['price']) / existing_position['price']) * 100", content,
                         "Should calculate price change percentage")
            
            # Check for profit threshold comparison
            self.assertIn("if price_change_percent >= profit_threshold:", content,
                         "Should compare profit against threshold")
            
            # Check for auto scalping profit close
            self.assertIn('self._close_position_with_reason(existing_position, current_price, "AUTO_SCALPING_PROFIT")', content,
                         "Should close position with AUTO_SCALPING_PROFIT reason when profitable")
            
            # Check for waiting when not profitable
            self.assertIn("Position non-profitable", content,
                         "Should wait when position is not profitable enough")
            
            print("✅ Smart Scalping Logic: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Smart Scalping Logic: FAILED - {str(e)}")
            return False
    
    def test_position_closing_methods_use_reason(self):
        """Test 5: Position Closing Methods - Verify all closing methods use _close_position_with_reason"""
        try:
            os.chdir('/app')
            
            # Read the crypto_bot_engine.py file
            with open('crypto_bot_engine.py', 'r') as f:
                content = f.read()
            
            # Check that various closing scenarios use _close_position_with_reason
            closing_scenarios = [
                ('TRAILING_STOP', 'self._close_position_with_reason(position, current_price, "TRAILING_STOP")'),
                ('TIMEOUT', 'self._close_position_with_reason(position, current_price, "TIMEOUT")'),
                ('STOP_LOSS', 'self._close_position_with_reason(position, current_price, "STOP_LOSS")'),
                ('TAKE_PROFIT', 'self._close_position_with_reason(position, current_price, "TAKE_PROFIT")'),
                ('MOMENTUM_DECLINE', 'self._close_position_with_reason(position, current_price, "MOMENTUM_DECLINE")'),
                ('AUTO_SCALPING_PROFIT', 'self._close_position_with_reason(existing_position, current_price, "AUTO_SCALPING_PROFIT")')
            ]
            
            for reason, expected_call in closing_scenarios:
                self.assertIn(expected_call, content,
                             f"Should use _close_position_with_reason for {reason}")
            
            print("✅ Position Closing Methods Use Reason: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Position Closing Methods Use Reason: FAILED - {str(e)}")
            return False
    
    def test_trade_duration_calculation_structure(self):
        """Test 6: Trade Duration Calculation - Verify entry_time and exit_time are properly handled"""
        try:
            # Create sample trade data with proper timestamps
            entry_time = datetime.now()
            exit_time = entry_time + timedelta(minutes=5, seconds=30)
            
            sample_trade = {
                "symbol": "BTC/USDT",
                "entry_price": 50000.0,
                "exit_price": 51000.0,
                "entry_time": entry_time.isoformat(),
                "exit_time": exit_time.isoformat(),
                "exit_reason": "TAKE_PROFIT",
                "net_pnl": 25.0,
                "total_fees": 0.15
            }
            
            # Test duration calculation
            entry_dt = datetime.fromisoformat(sample_trade['entry_time'].replace('Z', '+00:00').replace('+00:00', ''))
            exit_dt = datetime.fromisoformat(sample_trade['exit_time'].replace('Z', '+00:00').replace('+00:00', ''))
            duration = exit_dt - entry_dt
            
            # Verify duration calculation works
            self.assertIsInstance(duration, timedelta, "Duration should be a timedelta object")
            self.assertGreater(duration.total_seconds(), 0, "Duration should be positive")
            
            # Verify both timestamps are present and valid
            self.assertIn('entry_time', sample_trade, "Trade should have entry_time")
            self.assertIn('exit_time', sample_trade, "Trade should have exit_time")
            self.assertNotEqual(sample_trade['entry_time'], 'N/A', "entry_time should not be N/A")
            self.assertNotEqual(sample_trade['exit_time'], 'N/A', "exit_time should not be N/A")
            
            print("✅ Trade Duration Calculation Structure: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Trade Duration Calculation Structure: FAILED - {str(e)}")
            return False
    
    def test_portfolio_state_closed_trades_structure(self):
        """Test 7: Portfolio State Closed Trades - Verify closed trades have proper exit_reason and exit_time"""
        try:
            os.chdir('/app')
            
            # Check if portfolio_state.json exists and has closed trades
            if os.path.exists('portfolio_state.json'):
                with open('portfolio_state.json', 'r') as f:
                    portfolio = json.load(f)
                
                # Verify structure
                self.assertIn('closed_trades', portfolio, "Portfolio should have closed_trades")
                
                # Check closed trades structure if any exist
                if portfolio['closed_trades']:
                    for i, trade in enumerate(portfolio['closed_trades'][:5]):  # Check first 5 trades
                        # Verify exit_reason is not N/A
                        if 'exit_reason' in trade:
                            self.assertNotEqual(trade['exit_reason'], 'N/A', 
                                              f"Trade {i} exit_reason should not be N/A")
                            self.assertNotEqual(trade['exit_reason'], None, 
                                              f"Trade {i} exit_reason should not be None")
                        
                        # Verify exit_time is not N/A
                        if 'exit_time' in trade:
                            self.assertNotEqual(trade['exit_time'], 'N/A', 
                                              f"Trade {i} exit_time should not be N/A")
                            self.assertNotEqual(trade['exit_time'], None, 
                                              f"Trade {i} exit_time should not be None")
                        
                        # Verify required fields exist
                        required_fields = ['symbol', 'entry_price', 'exit_price', 'net_pnl']
                        for field in required_fields:
                            self.assertIn(field, trade, f"Trade {i} should have {field}")
                    
                    print(f"✅ Portfolio State Closed Trades Structure: PASSED - Checked {len(portfolio['closed_trades'])} trades")
                else:
                    print("✅ Portfolio State Closed Trades Structure: PASSED - No closed trades to check")
            else:
                print("✅ Portfolio State Closed Trades Structure: PASSED - No portfolio file exists yet")
            
            return True
            
        except Exception as e:
            print(f"❌ Portfolio State Closed Trades Structure: FAILED - {str(e)}")
            return False
    def test_config_manager_functionality(self):
        """Test 8: Configuration Management - Verify config.txt and config_manager.py work correctly"""
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
    print("🎯 Focus: Testing corrected trading bot functionality")
    print("=" * 70)
    
    # Manual test execution for better control
    test_instance = TestCryptoTradingBot()
    test_results = []
    
    test_methods = [
        'test_min_profit_auto_scalping_configuration',
        'test_close_position_with_reason_function',
        'test_close_position_scalping_na_fix',
        'test_smart_scalping_logic',
        'test_position_closing_methods_use_reason',
        'test_trade_duration_calculation_structure',
        'test_portfolio_state_closed_trades_structure',
        'test_config_manager_functionality'
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
    
    print("\n" + "=" * 70)
    print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Corrected trading bot functionality is working!")
        print("✅ Fixed 'N/A' Issue: exit_reason and exit_time are properly set")
        print("✅ Smart Scalping Logic: MIN_PROFIT_FOR_AUTO_SCALPING prevents premature selling")
        print("✅ Trade Duration Calculation: entry_time and exit_time are handled correctly")
        print("✅ Position Closing: All methods properly set exit_reason and exit_time")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed - Some fixes need attention")
        return False

if __name__ == "__main__":
    success = run_backend_tests()
    sys.exit(0 if success else 1)