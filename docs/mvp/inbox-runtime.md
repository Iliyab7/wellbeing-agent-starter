# Private file intake

Dot can open and summarize the first file using its existing connector. Use this optional executor when the participant wants structured continuity and the host has authorized private storage. The network path ends at Gmail or Drive. These commands read a file locally.

```sh
python scripts/inbox.py --home PRIVATE_STATE init --timezone UTC+03:30
python scripts/inbox.py --home PRIVATE_STATE scope --timezone UTC+03:30 --retention-days 30 --categories metrics workouts
python scripts/inbox.py --home PRIVATE_STATE import PRIVATE_ATTACHMENT.json --stream health-metrics --observed-at 2026-11-18T09:00:00+03:30
python scripts/inbox.py --home PRIVATE_STATE status
python scripts/inbox.py --home PRIVATE_STATE records --category metrics --metric step_count --limit 14
```

Paths, timezone, categories, retention and timestamp in this example are examples. Reuse existing settings or obtain applicable choices before applying scope. Select one stable stream per phone automation. Supply the connected provider's observed message-delivery or file-version timestamp, with offset, as `--observed-at`. Import previously unseen initial history in order from oldest to newest per stream. The official envelope is JSON v2. The importer accepts attachment bytes via stdin when the path is `-`.

The store is the existing private SQLite runtime. Approved category scope, replay and correction logic still apply. A transaction records the attachment digest and source time along with the import. Within retention, an exact file replay under the same stream returns `already_imported`. An unseen file with an older or equal source time returns `older_export`; review it before attempting historical backfill. A newly delivered message may contain older observation times, so never use email delivery as observation time. Keep the scope stable when processing a batch. Changing allowed categories clears the file cursor history to allow a fresh scoped import. Keep source attachments and temporary copies within agreed retention. Records output is for the authorized private executor.

The command does not connect an account or read Gmail by itself. Use real connector evidence in [INSTALL](../../INSTALL.md). A successful local import proves parsing and persistence of supplied data. Verify phone origin, attachment contents and the actual scheduled read before claiming live operation.
