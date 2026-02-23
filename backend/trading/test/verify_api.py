import asyncio
import sys
import os
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# Add backend to path (backend/trading/test -> ../../ -> backend)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Patch DB dependencies
sys.modules['core.database'] = MagicMock()
sys.modules['core.database'].AsyncSessionLocal = MagicMock()
sys.modules['app.domains.log.logger'] = MagicMock()

# Patch Strategy dependencies
sys.modules['pandas_ta'] = MagicMock()
sys.modules['trading.strategies.rsi_bb_strategy'] = MagicMock()

from app.main import app
from trading.bot import TradingBot

class TestBotControlAPI(unittest.TestCase):
    def setUp(self):
        # Create a mock bot
        self.mock_bot = MagicMock(spec=TradingBot)
        self.mock_bot.is_active = False # Initial state property Mock
        self.mock_bot.state = {"is_active": False}
        self.mock_bot.strategy_name = "TEST_STRATEGY"
        
        # Mock set_active method
        self.mock_bot.set_active = AsyncMock()
        
        # Mock get_snapshot method
        self.mock_bot.get_snapshot = AsyncMock(return_value={
            "is_active": False,
            "strategy_name": "TEST_STRATEGY",
            "balance": 10000,
            "is_holding": False,
            "avg_buy_price": 0,
            "target_price": 0,
            "stop_loss": 0,
            "last_reason": "",
            "timestamp": "2024-01-01T00:00:00",
        })
        
        # Mock loader
        self.mock_bot.loader = MagicMock()
        self.mock_bot.loader.get_current_price = AsyncMock(return_value=50000000)

        # Inject mock bot into app.state
        app.state.bot = self.mock_bot
        
        # Create TestClient
        self.client = TestClient(app)

    def test_start_bot(self):
        """Test POST /api/bot/start"""
        print("\n[Test] POST /api/bot/start")
        
        # 1. Normal Start
        self.mock_bot.is_active = False
        self.mock_bot.state['is_active'] = False
        
        response = self.client.post("/api/bot/start")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "bot started", "is_active": True})
        self.mock_bot.set_active.assert_called_with(True)
        print("-> Bot started successfully.")

        # 2. Idempotency (Already Started)
        # Update mock state to simulate active
        self.mock_bot.is_active = True 
        self.mock_bot.state['is_active'] = True
        self.mock_bot.set_active.reset_mock()
        
        response = self.client.post("/api/bot/start")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "already started", "is_active": True})
        self.mock_bot.set_active.assert_not_called()
        print("-> Idempotency check passed (already started).")

    def test_stop_bot(self):
        """Test POST /api/bot/stop"""
        print("\n[Test] POST /api/bot/stop")
        
        # 1. Normal Stop
        self.mock_bot.is_active = True
        self.mock_bot.state['is_active'] = True
        
        response = self.client.post("/api/bot/stop")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "bot stopped", "is_active": False})
        self.mock_bot.set_active.assert_called_with(False)
        print("-> Bot stopped successfully.")

        # 2. Idempotency (Already Stopped)
        self.mock_bot.is_active = False 
        self.mock_bot.state['is_active'] = False
        self.mock_bot.set_active.reset_mock()
        
        response = self.client.post("/api/bot/stop")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "already stopped", "is_active": False})
        self.mock_bot.set_active.assert_not_called()
        print("-> Idempotency check passed (already stopped).")

    def test_get_status(self):
        """Test GET /api/bot/status"""
        print("\n[Test] GET /api/bot/status")
        
        response = self.client.get("/api/bot/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["strategy_name"], "TEST_STRATEGY")
        self.assertEqual(data["balance"], 10000)
        self.assertIn("profit_rate", data)
        
        self.mock_bot.get_snapshot.assert_called_once()
        print("-> Status retrieved successfully.")

if __name__ == '__main__':
    unittest.main()
