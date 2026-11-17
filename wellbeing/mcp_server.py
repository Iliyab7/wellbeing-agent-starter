"""Official MCP v1 SDK stdio interface. Stdout belongs exclusively to the protocol."""
import os
from mcp.server.fastmcp import FastMCP
from .database import Database
from .service import Service, require_role


def create_mcp(home=None, token=None, public_url=None):
    db = Database(home); service = Service(db)
    credential = token if token is not None else os.environ.get('WELLBEING_ROLE_TOKEN', '')
    base = public_url if public_url is not None else os.environ.get('WELLBEING_PUBLIC_URL', '')
    mcp = FastMCP('Wellbeing MVP')

    def principal():
        return db.principal(credential)

    @mcp.tool()
    def wellbeing_status() -> dict:
        """Scoped observations and actual receipts; transport does not establish device acceptance."""
        return service.status(principal())

    @mcp.tool()
    def wellbeing_records(category: str | None = None, metric: str | None = None, limit: int = 100) -> list:
        """Read role-authorized Health evidence without summing or interpreting unknown values."""
        return service.records(principal(), category, metric, limit)

    @mcp.tool()
    def wellbeing_entries(kind: str | None = None) -> list:
        """Read scoped entries. Ordinary host/manager reads exclude emotional notes."""
        return service.entries(principal(), kind)

    @mcp.tool()
    def wellbeing_record_entry(entry: dict) -> dict:
        """Store source-message-backed entry/correction. Host supplies real vision/transcription.

        Meal payload requires meal,occurred_at with timezone,source_kind; photo_estimate
        requires nutrient_certainty=estimate. Skipped/declined meals are not zero food.
        """
        return service.write_entry(principal(), entry)

    @mcp.tool()
    def wellbeing_tasks() -> list:
        """List scoped task IDs and states; definitions are not spawned agents."""
        return service.tasks(principal())

    @mcp.tool()
    def wellbeing_task(operation: str, task: dict) -> dict | None:
        """create/claim/get/report/review/close bounded work. Claim returns minimum evidence.

        create: id,role,objective,acceptance,evidence_ids. report: id,claim_token,result,
        uncertainty. review: id,decision accept/revise,reason. Different role reviews.
        """
        return service.task(principal(), operation, task)

    @mcp.tool()
    def wellbeing_packet() -> dict:
        """Get prepared sections and scoped evidence for the host's attention decision."""
        return service.packet(principal())

    @mcp.tool()
    def wellbeing_configure(settings: dict) -> dict:
        """Apply actual participant choices. Scope reductions invalidate derived copies.

        Capability status verified requires receipt_ref and checked_at. Native instances
        require instance_id and receipt_ref. These are host attestations, not native creation.
        """
        return service.configure(principal(), settings)

    @mcp.tool()
    def wellbeing_pairing() -> dict:
        """Create private expiring single-use phone setup link using configured public HTTPS URL."""
        return service.create_pairing(principal(), base)

    @mcp.tool()
    def wellbeing_delivery_claim() -> list:
        """Claim pending output for actual host channel. Never automatically resend expired leases.

        Use idempotency_key with channel if supported. Send before lease_until, respect
        cancellation and reconcile uncertain results. This tool itself sends nothing.
        """
        p = principal(); require_role(p, 'host'); service.active(p)
        service.tick(p['participant'])
        return service.claim_outbox(p)

    @mcp.tool()
    def wellbeing_delivery_ack(delivery: dict) -> dict:
        """Record actual receipt_ref plus id and claim_token; delivery does not establish reading."""
        return service.acknowledge(principal(), delivery)

    @mcp.tool()
    def wellbeing_delivery_reconcile(delivery: dict) -> dict:
        """Host supplies id,outcome delivered/not_sent/unknown,receipt_ref after channel lookup.

        Retry only after confirmed not_sent. Unknown stays uncertain without auto resend.
        """
        return service.reconcile_delivery(principal(), delivery)

    @mcp.tool()
    async def wellbeing_opengym(operation: str, arguments: dict) -> dict:
        """Optional configured OpenGym read/search/preview. Writes and media extraction disabled."""
        from .opengym import OpenGym
        p = principal(); require_role(p, 'host', 'manager', 'analyst', 'coach')
        cfg = service.active(p)
        if not cfg['opengym']['enabled']:
            return {'status': 'not_configured'}
        return await OpenGym.from_environment(db.home).run(operation, arguments)

    return mcp


def main():
    create_mcp().run(transport='stdio')


if __name__ == '__main__':
    main()
