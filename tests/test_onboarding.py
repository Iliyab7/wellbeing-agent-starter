"""Synthetic link-only acceptance. The fake adapter has no scheduler or channel."""
import copy
from dataclasses import replace
import unittest

from wellbeing.onboarding import (Finding, Listing, Page, Source, completion_gaps,
                                  discover_sources, monitoring_plan, review_inventory)


class FreshHost:
    """Two metadata pages, no prior Sheet, no participant hint or health-name filter."""

    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.opened = []
        self.sheet = None
        self.writable = True
        self.sources = {
            "calendar": self.source("calendar", "appointments"),
            "classes": self.source("classes", "weekly timetable"),
            "SyncFit": self.source("SyncFit", "activity export"),
            portfolio: self.source(portfolio, "own portfolio, goals and practice journal"),
        }
        # Private synthetic files. A document can contain unrelated text.
        self.documents = {
            "calendar": [("week/2", "November", "Reminder: practice")],
            "classes": [("term/plan", "autumn term", "Classes: eight")],
            "SyncFit": [("export/day", "Nov 2", "Activity: walk")],
            portfolio: [
                ("portfolio/roles", "spring", "Role: workshop host\nWebsite colors: teal"),
                ("notes/goals", "March", "Goal: weekly practice"),
                ("notes/habits", "April", "Preference: morning sessions"),
            ],
        }

    @staticmethod
    def source(key, scope):
        return Source(key, scope, "Jan–Nov", "listed in participant account", "once",
                      identity_verified=True, revision="r1")

    def inventory(self, link):
        if link != "https://example.test/starter":
            raise ValueError("Fixture starts with the package link alone")
        sources, self.listing_gaps = discover_sources(["workspace index"], self.list_metadata)
        return sources

    def list_metadata(self, connection, cursor):
        candidates = list(self.sources.values())
        start = int(cursor or "0")
        end = start + 3
        return Listing(tuple(candidates[start:end]), str(end) if end < len(candidates) else "")

    def read_page(self, source, cursor):
        self.opened.append((source.key, cursor))
        if source.permission == "metadata" or not source.identity_verified:
            raise AssertionError("Content opened without scoped permission")
        documents = self.documents[source.key]
        if not documents:
            return Page("complete folder listing, Jan–Nov", ())
        offset = int(cursor or "0")
        path, window, body = documents[offset]
        # Deterministic extractor for this fixture's tiny document format.
        # A real host's Analyst makes this relevance/interpretation decision.
        limits = {
            "Role": "Past commitment", "Goal": "Past self-report",
            "Preference": "Check current preference", "Reminder": "Prompt only",
            "Classes": "Attendance unknown", "Activity": "One recorded day",
        }
        findings = []
        for line in body.splitlines():
            field, _, value = line.partition(": ")
            if field in limits:
                findings.append(Finding(path, window, f"{field}: {value}", limits[field]))
        following = str(offset + 1) if offset + 1 < len(documents) else ""
        return Page(path, tuple(findings), following)

    def run(self):
        inventory = self.inventory("https://example.test/starter")
        reviews = review_inventory(inventory, self.read_page, self.sheet)
        if self.writable:
            self.sheet = copy.deepcopy(reviews)
        return reviews, completion_gaps(inventory, reviews, self.sheet,
                                        listing_complete=not self.listing_gaps)


class OnboardingTests(unittest.TestCase):
    def test_link_only_baseline_and_readback_without_scheduler(self):
        for name in ("Kiln", "folio-79"):
            with self.subTest(name=name):
                host = FreshHost(name)
                reviews, gaps = host.run()
                self.assertEqual([], gaps)
                self.assertEqual({"calendar", "classes", "SyncFit", name}, set(reviews))
                self.assertEqual((
                    Finding("portfolio/roles", "spring", "Role: workshop host", "Past commitment"),
                    Finding("notes/goals", "March", "Goal: weekly practice", "Past self-report"),
                    Finding("notes/habits", "April", "Preference: morning sessions",
                            "Check current preference"),
                ), host.sheet[name].findings)
                self.assertEqual([(name, ""), (name, "1"), (name, "2")],
                                 [op for op in host.opened if op[0] == name])
                host.opened.clear()
                host.run()
                self.assertEqual([], host.opened)

    def test_first_useful_hit_or_omitted_profile_fails_even_after_write(self):
        host = FreshHost("Kiln")
        reviews, _ = host.run()
        inventory = host.inventory("https://example.test/starter")
        for keys in ([], ["SyncFit"], ["calendar", "classes", "SyncFit"]):
            short = {k: reviews[k] for k in keys}
            self.assertTrue(completion_gaps(inventory, short, copy.deepcopy(short),
                                            listing_complete=True))
        stored = dict(reviews, Kiln=replace(reviews["Kiln"], findings=()))
        self.assertTrue(completion_gaps(inventory, reviews, stored, listing_complete=True))
        self.assertTrue(completion_gaps(inventory, reviews, reviews, listing_complete=False))

    def test_pending_metadata_only_then_resume_after_scoped_grant(self):
        host = FreshHost("Kiln")
        grant = host.sources["Kiln"]
        host.sources["Kiln"] = replace(grant, permission="metadata")
        reviews, gaps = host.run()
        self.assertTrue(gaps)
        self.assertEqual("pending", host.sheet["Kiln"].status)
        self.assertFalse(any(key == "Kiln" for key, _ in host.opened))
        self.assertTrue(all(reviews[k].findings for k in ("calendar", "classes", "SyncFit")))
        host.sources["Kiln"] = grant
        host.opened.clear()
        _, gaps = host.run()
        self.assertEqual([], gaps)
        self.assertEqual({"Kiln"}, {key for key, _ in host.opened})

    def test_disconnected_and_absent_export(self):
        host = FreshHost("Kiln")
        host.sources["calendar"] = replace(host.sources["calendar"], unavailable="Reconnect")
        host.documents["SyncFit"] = []
        rows, gaps = host.run()
        self.assertTrue(gaps)
        self.assertEqual("unavailable", rows["calendar"].status)
        self.assertEqual("without_findings", rows["SyncFit"].status)
        self.assertEqual((), rows["SyncFit"].findings)
        self.assertEqual(3, len(host.sheet["Kiln"].findings))

    def test_clipped_or_failed_page_keeps_profile_partial(self):
        for mode in ("clipped", "failed", "loop"):
            with self.subTest(mode=mode):
                host = FreshHost("Kiln")
                original = host.read_page

                def broken(source, cursor):
                    if source.key == "Kiln" and cursor == "1":
                        if mode == "failed":
                            raise OSError("synthetic outage")
                        page = original(source, cursor)
                        return replace(page, truncated=True,
                                       next_cursor=cursor if mode == "loop" else "")
                    return original(source, cursor)

                host.read_page = broken
                rows, gaps = host.run()
                self.assertTrue(gaps)
                self.assertEqual("incomplete", rows["Kiln"].status)
                self.assertTrue(host.sheet["Kiln"].next_step)
                self.assertLess(len(rows["Kiln"].findings), 3)
                host.read_page = original
                host.opened.clear()
                _, gaps = host.run()
                self.assertEqual([], gaps)
                self.assertEqual({"Kiln"}, {key for key, _ in host.opened})
                self.assertEqual(3, len(host.sheet["Kiln"].findings))

    def test_no_writer_completes_authorized_reads(self):
        host = FreshHost("Kiln")
        host.writable = False
        rows, gaps = host.run()
        self.assertEqual(3, len(rows["Kiln"].findings))
        self.assertIsNone(host.sheet)
        self.assertIn("Baseline and coverage readback unverified", gaps)

    def test_recurring_scope_and_scheduler_are_independent_of_baseline(self):
        host = FreshHost("Kiln")
        _, gaps = host.run()
        self.assertEqual([], gaps)
        settings = dict(ongoing_sheet_access=True, scheduler_available=True, stopped=False)
        self.assertEqual((), monitoring_plan(host.sources, **settings)[0])
        host.sources["classes"] = replace(host.sources["classes"], permission="ongoing")
        self.assertEqual(("classes",), monitoring_plan(host.sources, **settings)[0])
        settings["scheduler_available"] = False
        scope, status = monitoring_plan(host.sources, **settings)
        self.assertEqual((), scope)
        self.assertIn("scheduler unavailable", status)

    def test_clipped_index_with_hidden_candidate_keeps_setup_partial(self):
        host = FreshHost("Kiln")
        page = host.list_metadata("workspace index", "")
        host.list_metadata = lambda connection, cursor: replace(page, next_cursor="", truncated=True)
        rows, gaps = host.run()
        self.assertNotIn("Kiln", rows)
        self.assertTrue(rows["SyncFit"].findings)
        self.assertIn("workspace index", host.listing_gaps)
        self.assertIn("Source inventory unverified", gaps)

    def test_unrelated_metadata_and_changed_source_on_resume(self):
        host = FreshHost("Kiln")
        host.sources["template"] = replace(host.source("template", "public catalog"),
                                           irrelevant="Blank stationery templates")
        rows, gaps = host.run()
        self.assertEqual([], gaps)
        self.assertEqual("irrelevant", rows["template"].status)
        self.assertFalse(any(key == "template" for key, _ in host.opened))
        host.sources["Kiln"] = replace(host.sources["Kiln"], revision="r2")
        host.documents["Kiln"][-1] = ("notes/habits", "June", "Preference: evenings")
        host.opened.clear()
        host.run()
        self.assertEqual({"Kiln"}, {key for key, _ in host.opened})
        self.assertEqual("Preference: evenings", host.sheet["Kiln"].findings[-1].summary)
