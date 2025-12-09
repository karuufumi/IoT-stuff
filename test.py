import unittest

from iot import gateway


class TestGateway(unittest.TestCase):
    def setUp(self):
        self.gateway = gateway.create_mqtt_client()

    def test_initialization(self):
        self.assertEqual(self.gateway.username, "test_user")
        self.assertEqual(self.gateway.key, "test_key")
        self.assertFalse(self.gateway.running)

    def test_start_stop(self):
        self.gateway.start()
        self.assertTrue(self.gateway.running)
        self.gateway.stop()
        self.assertFalse(self.gateway.running)

    def test_get_status(self):
        status = self.gateway.get_status()
        self.assertIsInstance(status, dict)
        self.assertIn("rt", status)
        self.assertIn("rh", status)
        self.assertIn("lux", status)

if __name__ == "__main__":
    unittest.main()