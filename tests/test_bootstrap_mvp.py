"""Synthetic private installation/resume tests; no network dependency installation here."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.bootstrap import bootstrap
from scripts.doctor import doctor
from wellbeing.database import Database


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    def test_twice_preserves_secrets_data_and_public_url(self):
        first = bootstrap(self.home, 'https://synthetic.example.test')
        credentials = (self.home / 'credentials.private.json').read_bytes()
        db = Database(self.home)
        with db.connect() as c:
            c.execute("INSERT INTO entries VALUES('owner','synthetic','meal','host','{}','2099-01-01T00:00:00+00:00')")
        second = bootstrap(self.home)
        self.assertEqual(credentials, (self.home / 'credentials.private.json').read_bytes())
        self.assertEqual(first['public_url'], second['public_url'])
        config = json.loads((self.home / 'mcp.private.json').read_text(encoding='utf-8'))
        self.assertEqual(len(config['mcpServers']), 5)
        for server in config['mcpServers'].values():
            self.assertEqual(server['env']['WELLBEING_PUBLIC_URL'], first['public_url'])
        with db.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM entries').fetchone()[0], 1)
        self.assertNotIn(json.loads(credentials)['host'], json.dumps(second))

    def test_missing_credentials_does_not_reprovision(self):
        bootstrap(self.home)
        (self.home / 'credentials.private.json').unlink()
        with self.assertRaises(ValueError):
            bootstrap(self.home)
        with Database(self.home).connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM tokens').fetchone()[0], 6)

    def test_invalid_public_url_has_no_install_side_effect(self):
        target = self.home / 'not-created'
        with self.assertRaises(ValueError):
            bootstrap(target, 'http://localhost')
        self.assertFalse(target.exists())

    def test_doctor_does_not_initialize_missing_store(self):
        target = self.home / 'absent'
        self.assertFalse(doctor(target)['initialized'])
        self.assertFalse(target.exists())
