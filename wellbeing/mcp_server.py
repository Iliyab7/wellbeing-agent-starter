"""Official SDK stdio tools; role credential supplied by private host configuration."""
import os
from mcp.server.fastmcp import FastMCP
from .database import Database
from .service import Service


def create_mcp(home=None, token=None):
    db = Database(home)
    service = Service(db)
    credential = token or os.environ.get('WELLBEING_ROLE_TOKEN', '')
    mcp = FastMCP('Wellbeing MVP')

    def principal():
        return db.principal(credential)

    @mcp.tool()
    def wellbeing_status() -> dict:
        """Actual intake freshness, roles and pending delivery count; not health interpretation."""
        return service.status(principal())

    @mcp.tool()
    def wellbeing_records(category: str | None = None, metric: str | None = None, limit: int = 100) -> list:
        """Read only role-authorized Health evidence, preserving source, units and timestamps."""
        return service.records(principal(), category, metric, limit)

    @mcp.tool()
    def wellbeing_entries(kind: str | None = None) -> list:
        """Read role-scoped meal/workout/context/findings or restricted emotional notes."""
        return service.entries(principal(), kind)

    @mcp.tool()
    def wellbeing_record_entry(entry: dict) -> dict:
        """Persist a real source-message-backed report, correction, finding, plan or prepared packet.

        Meal: {id,kind:'meal',payload:{meal,occurred_at,source_kind,description,...}}.
        Photo nutrients require nutrient_certainty:'estimate'. Do not fabricate transcription.
        """
        return service.write_entry(principal(), entry)

    @mcp.tool()
    def wellbeing_task(operation: str, task: dict) -> dict | None:
        """Create/claim/report/review/close bounded team work; actual host performs inference.

        create: id,role,objective,acceptance,evidence_ids. claim: {}. report: id,
        claim_token,result,uncertainty. review: id,decision accept/revise,reason. close: id.
        """
        return service.task(principal(), operation, task)

    @mcp.tool()
    def wellbeing_packet() -> dict:
        """Get evidence and prepared sections for Manager/CoS newsletter; not a diagnosis."""
        return service.packet(principal())

    @mcp.tool()
    def wellbeing_configure(settings: dict) -> dict:
        """Apply participant-authorized scope/timezone/meal times/pause. Only host or manager.

        Setting scopes cancels stale queued tasks and packets; confirm actual data recipients.
        """
        return service.configure(principal(), settings)

    @mcp.tool()
    def wellbeing_delivery_claim() -> list:
        """Host claims pending packets. Send through real authorized channel; ack actual receipt.

        No call to this tool sends a WhatsApp message. Host must have a real connector.
        """
        p = principal()
        if p['role'] == 'host':
            service.tick(p['participant'])
        return service.claim_outbox(p)

    @mcp.tool()
    def wellbeing_delivery_ack(delivery: dict) -> dict:
        """Record actual channel receipt with id,claim_token,receipt_ref; not read/adoption."""
        return service.acknowledge(principal(), delivery)

    return mcp


def main():
    create_mcp().run(transport='stdio')


if __name__ == '__main__':
    main()
