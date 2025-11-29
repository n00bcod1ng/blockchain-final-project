import unittest
import json
from blochchain import app

class BlockchainTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.network_key = "hospital-network-2025"

    def test_genesis_block(self):
        """Test that the blockchain starts correctly."""
        response = self.app.get('/chain')
        data = json.loads(response.data)
        self.assertEqual(data['length'], 1)
        self.assertEqual(data['chain'][0]['previous_hash'], "0")

    def test_mine_block(self):
        """Test the mining endpoint."""
        response = self.app.get(f'/mine?network_key={self.network_key}')
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()

    