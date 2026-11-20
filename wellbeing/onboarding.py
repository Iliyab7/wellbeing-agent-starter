"""Portable reference for the INSTALL.md source loop and initial-baseline gate.

Host adapters supply live, scoped metadata and minimized analyst results. This
module neither acquires authority nor opens accounts, Sheets or scheduled jobs.
"""
from dataclasses import dataclass, replace
from typing import Callable, Iterable, Literal, Mapping


@dataclass(frozen=True)
class Source:
    key: str                    # provider/account/object identity
    scope: str                  # participant-authorized purpose and range
    window: str                 # requested observation window
    probe: str                  # live read-only probe receipt or failure
    permission: Literal["metadata", "once", "ongoing"]
    # Set only after checking participant identity and scope.
    identity_verified: bool
    unavailable: str = ""
    irrelevant: str = ""        # reason supported by permitted metadata
    revision: str = ""          # reliable change token, if available


@dataclass(frozen=True)
class Listing:
    sources: tuple[Source, ...]
    next_cursor: str = ""
    truncated: bool = False


def discover_sources(
    connections: Iterable[str], list_metadata: Callable[[str, str], Listing],
) -> tuple[dict[str, Source], dict[str, str]]:
    """Enumerate *metadata-authorized* connections; retain failed index ranges."""
    sources, gaps = {}, {}
    for connection in connections:
        cursor = ""
        seen = set()
        while cursor not in seen:
            seen.add(cursor)
            try:
                page = list_metadata(connection, cursor)
            except OSError:
                gaps[connection] = f"Metadata read failed at {cursor or 'first page'}"
                break
            for source in page.sources:
                if source.key in sources and source != sources[source.key]:
                    gaps[connection] = "Conflicting source identity or scope"
                    # Defer the ambiguous candidate while other sources proceed.
                    sources[source.key] = replace(source, unavailable=gaps[connection])
                else:
                    sources[source.key] = source
            if not page.next_cursor:
                if page.truncated:
                    gaps[connection] = f"Clipped listing at {cursor or 'first page'}"
                break
            cursor = page.next_cursor
        else:
            gaps[connection] = f"Repeated listing continuation at {cursor}"
    return sources, gaps


@dataclass(frozen=True)
class Finding:
    document: str
    observed: str               # observation date/window
    summary: str
    use_and_limit: str


@dataclass(frozen=True)
class Page:
    reviewed: str               # actual document/range opened
    findings: tuple[Finding, ...]
    next_cursor: str = ""
    truncated: bool = False


@dataclass(frozen=True)
class Review:
    source: Source
    status: str
    ranges: tuple[str, ...] = ()
    findings: tuple[Finding, ...] = ()
    reason: str = ""
    next_step: str = ""
    cursor: str = ""


def review_source(source: Source, read_page: Callable[[Source, str], Page],
                  previous: Review | None = None) -> Review:
    """read_page opens only confirmed relevant ranges and extracts from content."""
    if source.unavailable or not source.probe:
        return Review(source, "unavailable", reason=source.unavailable or "No live probe",
                      next_step="Retry the scoped connection")
    if source.irrelevant:
        return Review(source, "irrelevant", reason=source.irrelevant)
    if source.permission not in ("once", "ongoing") or not source.identity_verified:
        return Review(source, "pending", reason="Scoped read or participant identity unconfirmed",
                      next_step="Resolve the missing authority or identity")

    ranges, findings, cursor = [], [], ""
    if (previous and source.revision and
            replace(previous.source, probe=source.probe) == source):
        if previous.status in ("with_findings", "without_findings"):
            return replace(previous, source=source)
        if previous.status == "incomplete" and previous.cursor:
            ranges.extend(previous.ranges)
            findings.extend(previous.findings)
            cursor = previous.cursor

    seen = set()
    while True:
        seen.add(cursor)
        try:
            page = read_page(source, cursor)
        except OSError:
            reason = "Scoped range could not be read"
            break
        if not page.reviewed:
            reason = "Missing evidence of the range opened"
            break
        ranges.append(page.reviewed)
        findings.extend(page.findings)
        if not page.next_cursor:
            if page.truncated:
                reason = "Clipped response without a continuation"
                cursor = ""
                break
            status = "with_findings" if findings else "without_findings"
            return Review(source, status, tuple(ranges), tuple(findings))
        if page.next_cursor in seen:
            reason = "Repeated continuation"
            cursor = ""
            break
        cursor = page.next_cursor
    return Review(source, "incomplete", tuple(ranges), tuple(findings), reason,
                  "Resume the missing range or use a narrower authorized read", cursor)


def review_inventory(inventory: Mapping[str, Source], read_page: Callable[[Source, str], Page],
                     previous: Mapping[str, Review] | None = None) -> dict[str, Review]:
    """Start from live listing results, even when another source yielded a finding."""
    verified = previous or {}
    return {key: review_source(source, read_page, verified.get(key))
            for key, source in inventory.items()}


def completion_gaps(inventory: Mapping[str, Source], reviews: Mapping[str, Review],
                    readback: Mapping[str, Review] | None, *,
                    listing_complete: bool) -> list[str]:
    """Compare independent inventory and expected rows to actual same-Sheet cells.

    The adapter supplies None for missing/failed reads or a different Sheet.
    A failed/truncated index stays open even if all visible rows are checked.
    """
    gaps = []
    if not listing_complete or not inventory:
        gaps.append("Source inventory unverified")
    if set(inventory) != set(reviews):
        gaps.append("Source inventory and review rows differ")
    for key, source in inventory.items():
        row = reviews.get(key)
        if not row or row.source != source or key != source.key:
            gaps.append(f"{key}: missing or stale review")
            continue
        if not (source.key and source.scope and source.window):
            gaps.append(f"{key}: missing source identity, scope or requested window")
            continue
        if row.status == "irrelevant" and source.irrelevant and row.reason:
            continue
        checked = (row.status == "with_findings" and bool(row.findings) or
                   row.status == "without_findings" and not row.findings)
        supported = all(f.document and f.observed and f.summary and f.use_and_limit
                        for f in row.findings)
        if not (checked and supported and row.ranges and source.probe and
                source.permission in ("once", "ongoing") and source.identity_verified
                and not source.unavailable):
            gaps.append(f"{key}: {row.reason or row.status}")
    if readback is None or readback != reviews:
        gaps.append("Baseline and coverage readback unverified")
    return gaps


def monitoring_plan(inventory: Mapping[str, Source], *, ongoing_sheet_access: bool,
                    scheduler_available: bool, stopped: bool) -> tuple[tuple[str, ...], str]:
    """Select the scope for step 6. An eligible plan still needs a real job readback."""
    if stopped or not ongoing_sheet_access:
        return (), "Inactive: recurring Sheet access missing or monitoring stopped"
    eligible = tuple(key for key, source in inventory.items()
                     if source.permission == "ongoing" and source.identity_verified
                     and not source.irrelevant)
    if not eligible:
        return (), "Inactive: no recurring source authority"
    if not scheduler_available:
        return (), "Inactive: scheduler unavailable; resume on next visit"
    return eligible, "Reconcile job and verify its settings"
