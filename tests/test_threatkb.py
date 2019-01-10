import os
import unittest
import tempfile


import testing_config
import app
from app.models.users import KBUser



class ThreatKBTestCase(unittest.TestCase):

    def setUp(self):
        app.app.config.from_object("testing_config")
        self.app = app.app.test_client()

        with app.app.app_context():
            # Reinitialize the db connection with testing values.
            app.db = app.get_db()
            app.init_db()
            
            # Register and log in a test user.
            self.register()
            self.login()


    def register(self):
        self.user = KBUser(
            email=testing_config.TEST_USER,
            password=testing_config.TEST_PASSWORD_HASHED,
            admin=True,
            active=True
        )
        app.db.session.add(self.user)
        app.db.session.commit()


    def login(self):
        return self.app.post('/ThreatKB/login', json=dict(
            email=testing_config.TEST_USER,
            password=testing_config.TEST_PASSWORD
        ), follow_redirects=True)


    def logout(self):
        return self.app.get('/ThreatKB/logout', follow_redirects=True)


    def test_empty_c2ip(self):
        rv = self.app.get('/ThreatKB/c2ips')
        self.assertEqual('{"total_count": 0, "data": []}', rv.data)


    def tearDown(self):
        # Log out.
        self.logout()

        # Unregister user.
        app.db.session.delete(self.user)
        app.db.session.commit()

        # Drop all tables.
        app.deinit_db()

if __name__ == '__main__':
    unittest.main()
