"""Actual official-SDK stdio subprocess roundtrip with synthetic private state."""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from wellbeing.database import Database
from wellbeing.service import Service


@unittest.skipUnless(importlib.util.find_spec('mcp'), 'Install requirements-mvp.txt for MCP process tests')
class MCPProcessTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialize_list_call_pair_and_role_denial(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as home:
            db = Database(home); keys = db.provision(); service = Service(db)
            service.configure(db.principal(keys['host']), {'categories': ['metrics'], 'role_categories': {'host': ['metrics'], 'analyst': ['metrics']}})
            for role in ('host', 'analyst'):
                env = {**os.environ, 'WELLBEING_MVP_HOME': home, 'WELLBEING_ROLE_TOKEN': keys[role], 'WELLBEING_PUBLIC_URL': 'https://synthetic.example.test'}
                params = StdioServerParameters(command=sys.executable, args=[str(root / 'scripts' / 'run_mcp.py')], env=env)
                async with asyncio.timeout(40):
                    async with stdio_client(params) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            listing = await session.list_tools()
                            names = {tool.name for tool in listing.tools}
                            self.assertIn('wellbeing_pairing', names)
                            self.assertIn('wellbeing_delivery_reconcile', names)
                            result = await session.call_tool('wellbeing_status', {})
                            self.assertFalse(result.isError)
                            rendered = ''.join(block.text for block in result.content if block.type == 'text')
                            self.assertIn(role, rendered)
                            pair = await session.call_tool('wellbeing_pairing', {})
                            if role == 'host':
                                self.assertFalse(pair.isError)
                                self.assertIn('/pair/', ''.join(b.text for b in pair.content if b.type == 'text'))
                            else:
                                self.assertTrue(pair.isError)
                            self.assertNotIn(keys[role], rendered)
