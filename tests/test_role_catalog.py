"""The MVP catalog must not expand legacy runtime permissions."""
import copy
from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from wellbeing import core


class LegacyCatalogTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2030, 1, 8, 12, tzinfo=timezone.utc)
        self.state = core.initialize('Synthetic catalog check', 'UTC', now=self.now)
        policy = core.read_json(core.ROOT / 'examples/policy.synthetic.json')
        core.configure(self.state, policy, confirmed=True, now=self.now)
        self.catalog = core.read_json(core.ROOT / 'agents/registry.json')
        if not any(entry['id'] == 'companion' for entry in self.catalog['team']):
            self.catalog['team'].append({
                'id': 'companion', 'instructions': 'agents/companion.md',
                'skills': ['skills/wellbeing-emotional-support/SKILL.md']})

    def manifest(self, catalog=None, mode='inline'):
        with patch.object(core, 'read_json', return_value=catalog or self.catalog):
            return core.team(self.state, mode, self.now)

    def test_four_role_catalog_projects_to_legacy_three_role_manifest(self):
        for mode in ('inline', 'native'):
            with self.subTest(mode=mode):
                self.state['policy']['authority']['create_subagents'] = True
                result = self.manifest(mode=mode)
                self.assertEqual(result['execution_status'], 'manifest_only')
                self.assertEqual([m['role'] for m in result['members']],
                                 ['manager', 'analyst', 'coach'])
                self.assertTrue(all(m['status'] == 'not_started' and m['tools'] == []
                                    for m in result['members']))
        old = copy.deepcopy(self.catalog)
        old['team'] = [e for e in old['team'] if e['id'] != 'companion']
        self.assertEqual(len(self.manifest(old)['members']), 3)

    def test_companion_has_no_legacy_permissions_or_packet_capability(self):
        self.assertNotIn('companion', core.ROLES)
        self.assertNotIn('companion', core.MEMBERS)
        for field in ('team_recipients', 'source_recipients'):
            with self.subTest(field=field):
                policy = copy.deepcopy(self.state['policy'])
                target = policy['team_recipients'] if field == 'team_recipients' else policy['sources'][0]['recipients']
                target.append('companion')
                with self.assertRaises(core.PilotError):
                    core.validate_policy(policy)
        with self.assertRaises(core.PilotError):
            core.packet(self.state, 'companion', 'Synthetic support', now=self.now)

    def test_native_authority_is_still_required(self):
        self.state['policy']['authority']['create_subagents'] = False
        self.assertEqual(self.manifest()['execution_status'], 'manifest_only')
        with self.assertRaises(core.PilotError):
            self.manifest(mode='native')

    def test_unknown_and_malformed_extensions_are_rejected(self):
        changes = [
            {'id': 'unknown_role'},
            {'instructions': 'agents/coach.md'},
            {'skills': []},
            {'skills': ['skills/wellbeing-emotional-support/SKILL.md'] * 2},
            {'skills': ['missing-synthetic-file.md']},
            {'skills': [None]},
        ]
        for change in changes:
            with self.subTest(change=change):
                catalog = copy.deepcopy(self.catalog)
                companion = next(e for e in catalog['team'] if e['id'] == 'companion')
                companion.update(change)
                with self.assertRaises(core.PilotError):
                    self.manifest(catalog)
        duplicate = copy.deepcopy(self.catalog)
        duplicate['team'].append(copy.deepcopy(duplicate['team'][-1]))
        with self.assertRaises(core.PilotError):
            self.manifest(duplicate)
        misplaced = copy.deepcopy(self.catalog)
        misplaced['interface'] = copy.deepcopy(next(e for e in misplaced['team'] if e['id'] == 'companion'))
        with self.assertRaises(core.PilotError):
            self.manifest(misplaced)
