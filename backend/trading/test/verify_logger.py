import unittest
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock

# Add backend to path (backend/trading/test -> ../../ -> backend)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Patch DB dependencies
sys.modules['core.database'] = MagicMock()
sys.modules['core.database'].AsyncSessionLocal = MagicMock()
sys.modules['app.domains.log.logger'] = MagicMock()

from trading.db_logger import save_log_to_db, _BACKUP_LOG_PATH

class TestLoggerFallback(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        if os.path.exists(_BACKUP_LOG_PATH):
            os.remove(_BACKUP_LOG_PATH)

    def tearDown(self):
        if os.path.exists(_BACKUP_LOG_PATH):
            os.remove(_BACKUP_LOG_PATH)

    async def test_logger_fallback_on_failure(self):
        """Test that backup.log is created when DB save fails 3 times"""
        print("\n[Test] Logger Fallback")
        
        # Mock AsyncSessionLocal to raise exception
        mock_session = MagicMock()
        mock_session.__aenter__.side_effect = Exception("DB Connection Refused")
        sys.modules['core.database'].AsyncSessionLocal.return_value = mock_session
        
        # Call save_log_to_db
        await save_log_to_db("INFO", "SYSTEM", "TEST", "Fallback Message")
        
        # Check file
        self.assertTrue(os.path.exists(_BACKUP_LOG_PATH), "Backup log file should exist")
        
        with open(_BACKUP_LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Fallback Message", content)
            print("-> OK")

if __name__ == '__main__':
    unittest.main()
