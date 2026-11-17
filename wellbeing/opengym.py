"""Optional official-SDK OpenGym client. No invented tool names or media extraction.

Private opengym.private.json: {"url":"https://approved-host/mcp",
"token_env":"OPENGYM_TOKEN","tools":{"search":"reviewed_advertised_tool"},
"review_receipt":"host review reference"}. Map only read/search/preview after
reviewing the actual server's tools. This file is not an installation receipt.
"""
from contextlib import asynccontextmanager
import asyncio
import os
from pathlib import Path
from .core import read_json
from .database import Denied, packed
from .iphone import validate_public_url

OPERATIONS = ('read', 'search', 'preview')


@asynccontextmanager
async def official_session(url, token):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    import httpx

    def private_client_factory(headers=None, timeout=None, auth=None):
        # MCP 1.30 owns client lifetime and passes headers/timeout/auth through
        # this supported factory. Never follow redirects carrying private headers.
        return httpx.AsyncClient(
            headers=headers,
            timeout=timeout if timeout is not None else httpx.Timeout(20),
            auth=auth,
            follow_redirects=False,
        )

    async with streamablehttp_client(
        url,
        headers={'Authorization': 'Bearer ' + token},
        timeout=20,
        httpx_client_factory=private_client_factory,
    ) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            yield session


class OpenGym:
    def __init__(self, config=None, token=None, session_factory=None):
        self.config = config or {}
        self.token = token
        self.session_factory = session_factory or official_session

    @classmethod
    def from_environment(cls, home):
        path = Path(home) / 'opengym.private.json'
        if not path.exists():
            return cls()
        if path.is_symlink():
            raise ValueError('Refusing symlink OpenGym configuration')
        cfg = read_json(path)
        if not isinstance(cfg, dict):
            raise ValueError('Invalid OpenGym configuration')
        env = cfg.get('token_env', 'OPENGYM_TOKEN')
        if not isinstance(env, str) or not env or not env.replace('_', '').isalnum():
            raise ValueError('Invalid token environment name')
        return cls(cfg, os.environ.get(env))

    async def run(self, operation, arguments):
        if operation not in (*OPERATIONS, 'status'):
            raise Denied('OpenGym writes and unreviewed operations are disabled')
        if not isinstance(arguments, dict) or len(packed(arguments)) > 32000:
            raise ValueError('Bounded argument object required')
        if not self.config or not self.token:
            return {'status': 'not_configured', 'writes_enabled': False}
        cfg = self.config
        if set(cfg) - {'url', 'token_env', 'tools', 'review_receipt'}:
            raise ValueError('Unknown OpenGym adapter fields')
        url = validate_public_url(cfg.get('url'))
        mapping = cfg.get('tools')
        if not isinstance(mapping, dict) or set(mapping) - set(OPERATIONS) or any(not isinstance(v, str) or not v for v in mapping.values()) or not isinstance(cfg.get('review_receipt'), str) or not cfg['review_receipt'].strip():
            raise ValueError('Explicit reviewed read/search/preview tool mapping required')
        if operation != 'status' and operation not in mapping:
            raise Denied('Operation not configured')
        try:
            async with asyncio.timeout(25):
                async with self.session_factory(url, self.token) as session:
                    advertised = {}; cursor = None
                    for _ in range(20):
                        listing = await session.list_tools(cursor=cursor)
                        for tool in listing.tools:
                            advertised[tool.name] = tool
                        cursor = getattr(listing, 'nextCursor', None)
                        if not cursor:
                            break
                    else:
                        return {'status': 'unavailable', 'reason': 'tool_catalog_limit'}
                    missing = set(mapping.values()) - set(advertised)
                    if missing:
                        return {'status': 'unavailable', 'reason': 'configured_tool_not_advertised'}
                    # Server annotations are advisory; reject explicitly destructive tools too.
                    for name in mapping.values():
                        annotations = getattr(advertised[name], 'annotations', None)
                        if annotations is not None and getattr(annotations, 'destructiveHint', None) is True:
                            raise Denied('Configured tool advertises destructive behavior')
                    if operation == 'status':
                        return {'status': 'ready', 'operations': sorted(mapping), 'writes_enabled': False,
                                'evidence': 'initialized_and_listed_tools', 'media': 'native_links_only'}
                    result = await session.call_tool(mapping[operation], arguments=arguments)
                    if getattr(result, 'isError', False):
                        return {'status': 'tool_error', 'operation': operation}
                    # Do not retrieve or forward images/audio/resources licensed to another app.
                    blocks = [{'type': 'text', 'text': block.text} for block in result.content if getattr(block, 'type', None) == 'text']
                    if len(packed(blocks)) > 131072:
                        return {'status': 'unavailable', 'reason': 'result_limit'}
                    return {'status': 'ok', 'operation': operation, 'content': blocks,
                            'trust': 'external_evidence_not_instructions', 'primary_memory_written': False}
        except Denied:
            raise
        except Exception:
            # Never expose exception strings containing endpoint, token or returned private data.
            return {'status': 'unavailable', 'reason': 'connection_or_protocol_failure', 'writes_enabled': False}
