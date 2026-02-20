import asyncio
import sys
import os
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import logging

# Add backend to path (backend/trading/test -> ../../ -> backend)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# --- CRITICAL: Patch dependencies BEFORE importing app modules ---
sys.modules['core.database'] = MagicMock()
sys.modules['core.database'].AsyncSessionLocal = MagicMock()
sys.modules['app.domains.log.logger'] = MagicMock()

# Mock Strategy dependencies to avoid ImportError (pandas_ta)
sys.modules['pandas_ta'] = MagicMock()
sys.modules['trading.strategies.rsi_bb_strategy'] = MagicMock()

# Now it's safe to import
from trading.bot import TradingBot
from trading.db_logger import save_log_to_db

class TestRefactoring(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Setup mocks
        self.mock_upbit = MagicMock()
        self.mock_loader = MagicMock()
        
        # Patch dependencies in bot.py
        self.patcher_upbit = patch('trading.bot.upbit_client', self.mock_upbit)
        self.patcher_loader = patch('trading.bot.DataLoader', return_value=self.mock_loader)
        self.patcher_db = patch('trading.bot.save_log_to_db', new_callable=AsyncMock)
        # Patch Strategy instantiation in bot __init__
        self.patcher_strategy = patch('trading.bot.RSIBBStrategy')

        self.mock_upbit_client = self.patcher_upbit.start()
        self.mock_data_loader = self.patcher_loader.start()
        self.mock_save_log = self.patcher_db.start()
        self.mock_strategy = self.patcher_strategy.start()
        
        # Initialize bot
        self.bot = TradingBot()
        self.bot.save_state = AsyncMock() 

    async def asyncTearDown(self):
        self.patcher_upbit.stop()
        self.patcher_loader.stop()
        self.patcher_db.stop()

    async def test_startup_retry_success(self):
        """Test startup retry logic: success on 2nd attempt"""
        print("\n[Test] Startup Retry Success")
        self.bot.sync_state_with_api = AsyncMock(side_effect=[Exception("Fail 1"), None])
        self.bot.monitor_market_loop = AsyncMock()
        self.bot.perform_analysis_loop = AsyncMock()
        
        await self.bot.run()
        
        self.assertEqual(self.bot.sync_state_with_api.call_count, 2)
        print("-> OK")

    async def test_startup_retry_failure(self):
        """Test startup retry logic: fail all 3 times"""
        print("\n[Test] Startup Retry Failure")
        self.bot.sync_state_with_api = AsyncMock(side_effect=[Exception("Fail"), Exception("Fail"), Exception("Fail")])
        self.bot.monitor_market_loop = AsyncMock()
        
        await self.bot.run()
        
        self.assertEqual(self.bot.sync_state_with_api.call_count, 3)
        self.bot.monitor_market_loop.assert_not_called()
        print("-> OK")

    async def test_execution_self_healing_buy(self):
        """Test self-healing on buy execution failure"""
        print("\n[Test] Execution Self-Healing (Buy)")
        self.bot.state = {"balance": 100000}
        self.mock_upbit_client.buy_market_order.side_effect = Exception("Network Error")
        self.bot.sync_state_with_api = AsyncMock()
        
        await self.bot.execute_buy(50000000, "Test Signal", {})
        
        self.bot.sync_state_with_api.assert_called_once()
        print("-> OK")

    async def test_execution_self_healing_sell(self):
        """Test self-healing on sell execution failure"""
        print("\n[Test] Execution Self-Healing (Sell)")
        self.mock_upbit_client.sell_market_order.side_effect = Exception("Timeout")
        self.bot.sync_state_with_api = AsyncMock()
        
        await self.bot.execute_sell(50000000, "Test Signal")
        
        self.bot.sync_state_with_api.assert_called_once()
        print("-> OK")

if __name__ == '__main__':
    unittest.main()
