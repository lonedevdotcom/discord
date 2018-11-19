import dbutils
import unittest

class TestServerDatabase(unittest.TestCase):

    def setUp(self):
        self.db = dbutils.ServerDatabase()

    def test_get_aliases_just_server(self):
        self.assertEqual(len(self.db.get_all_server_member_system_aliases(0)), 0)

    def test_get_aliases_server_and_member(self):
        self.assertEqual(len(self.db.get_all_server_member_system_aliases(0, 0)), 0)
