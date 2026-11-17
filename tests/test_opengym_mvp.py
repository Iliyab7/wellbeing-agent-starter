"""Synthetic adapter and official-session boundary tests; no network/media retrieval."""
from contextlib import asynccontextmanager
import importlib.util
import inspect
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from wellbeing.database import Denied
from wellbeing.opengym import OpenGym, official_session


class FakeSession:
    def __init__(self):
        self.calls = []

    async def list_tools(self, cursor=None):
        return NS(tools=[NS(name='reviewed_search', annotations=NS(destructiveHint=False))], nextCursor=None)

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return NS(isError=False, content=[NS(type='text', text='Synthetic native app link'), NS(type='image', data='not-forwarded')])


class OpenGymTests(unittest.IsolatedAsyncioTestCase):
    async def test_not_configured_and_writes_denied(self):
        adapter = OpenGym()
        self.assertEqual((await adapter.run('status', {}))['status'], 'not_configured')
        with self.assertRaises(Denied):
            await adapter.run('log_workout', {})

    async def test_reviewed_mapping_and_text_only_results(self):
        session = FakeSession()

        @asynccontextmanager
        async def factory(url, token):
            self.assertEqual(url, 'https://synthetic.example.test/mcp')
            self.assertEqual(token, 'synthetic-secret')
            yield session

        adapter = OpenGym({'url': 'https://synthetic.example.test/mcp', 'tools': {'search': 'reviewed_search'}, 'review_receipt': 'synthetic-review'}, 'synthetic-secret', factory)
        self.assertEqual((await adapter.run('status', {}))['status'], 'ready')
        result = await adapter.run('search', {'query': 'synthetic'})
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(len(result['content']), 1)
        self.assertFalse(result['primary_memory_written'])
        self.assertEqual(session.calls, [('reviewed_search', {'query': 'synthetic'})])
        with self.assertRaises(Denied):
            await adapter.run('preview', {})

    async def test_failure_redacts_exception(self):
        @asynccontextmanager
        async def broken(url, token):
            raise RuntimeError('synthetic-secret private payload')
            yield

        adapter = OpenGym({'url': 'https://synthetic.example.test/mcp', 'tools': {'search': 'reviewed_search'}, 'review_receipt': 'synthetic-review'}, 'synthetic-secret', broken)
        result = await adapter.run('search', {})
        self.assertEqual(result['status'], 'unavailable')
        self.assertNotIn('synthetic-secret', str(result))


@unittest.skipUnless(importlib.util.find_spec('mcp') and importlib.util.find_spec('httpx'), 'Install requirements-mvp.txt for official transport regression')
class OfficialSessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_supported_factory_signature_headers_redirects_and_lifecycle(self):
        import httpx
        from mcp.client.streamable_http import streamablehttp_client

        # Validate production call arguments against the actual installed SDK,
        # even though transport I/O is replaced below. The former http_client
        # keyword fails here rather than being hidden as adapter unavailable.
        sdk_signature = inspect.signature(streamablehttp_client)
        events = []
        clients = []
        read_stream, write_stream = object(), object()
        sdk_timeout = httpx.Timeout(17, read=91)
        sdk_auth = httpx.BasicAuth('synthetic-user', 'synthetic-password')

        @asynccontextmanager
        async def fake_transport(*args, **kwargs):
            bound = sdk_signature.bind(*args, **kwargs)
            self.assertEqual(bound.arguments['url'], 'https://synthetic.example.test/mcp')
            self.assertEqual(bound.arguments['timeout'], 20)
            self.assertEqual(bound.arguments['headers'], {'Authorization': 'Bearer synthetic-token'})
            factory = bound.arguments['httpx_client_factory']
            headers = {**bound.arguments['headers'], 'Mcp-Session-Id': 'synthetic-session'}
            client = factory(headers=headers, timeout=sdk_timeout, auth=sdk_auth)
            clients.append(client)
            self.assertIsInstance(client, httpx.AsyncClient)
            self.assertFalse(client.follow_redirects)
            self.assertEqual(client.headers['Authorization'], 'Bearer synthetic-token')
            self.assertEqual(client.headers['Mcp-Session-Id'], 'synthetic-session')
            self.assertEqual(client.timeout, sdk_timeout)
            self.assertIs(client.auth, sdk_auth)
            async with client:
                events.append('transport_enter')
                try:
                    yield read_stream, write_stream, lambda: 'synthetic-session'
                finally:
                    events.append('transport_exit')

        class Session(FakeSession):
            def __init__(self, read, write):
                super().__init__()
                self.streams = (read, write)

            async def __aenter__(self):
                events.append('session_enter')
                return self

            async def initialize(self):
                events.append('initialize')

            async def __aexit__(self, *exc):
                events.append('session_exit')

        with patch('mcp.client.streamable_http.streamablehttp_client', fake_transport), patch('mcp.ClientSession', Session):
            # Call official_session directly so signature/client failures cannot
            # be swallowed by OpenGym.run's redacted unavailable fallback.
            async with official_session('https://synthetic.example.test/mcp', 'synthetic-token') as session:
                self.assertEqual(session.streams, (read_stream, write_stream))
                self.assertEqual(events, ['transport_enter', 'session_enter', 'initialize'])
                listing = await session.list_tools()
                self.assertEqual(listing.tools[0].name, 'reviewed_search')
            self.assertEqual(events, ['transport_enter', 'session_enter', 'initialize', 'session_exit', 'transport_exit'])
            self.assertTrue(clients[0].is_closed)

            # Also exercise the adapter's default official_session binding.
            adapter = OpenGym({'url': 'https://synthetic.example.test/mcp', 'tools': {'search': 'reviewed_search'}, 'review_receipt': 'synthetic-review'}, 'synthetic-token')
            result = await adapter.run('search', {'query': 'synthetic'})
            self.assertEqual(result['status'], 'ok')
            self.assertEqual(result['content'], [{'type': 'text', 'text': 'Synthetic native app link'}])
            self.assertEqual(len(clients), 2)
            self.assertTrue(all(client.is_closed for client in clients))
