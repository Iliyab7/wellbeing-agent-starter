"""Executable private host job contract; provides no invented channel/model API.

Register a real recurring host job to run collect with its role token in
WELLBEING_ROLE_TOKEN. --output MUST be private/outside the repository. The host
reads that job file, loads the named role instructions, performs actual reasoning
or channel calls, and writes results to another private JSON file. Run apply with
--results to persist those actual results. Use separate specialist credentials;
never give the host credential to a specialist worker.

Delivery results: {deliveries:[{id,claim_token,receipt_ref}]}.
Uncertain sends: {reconciliations:[{id,outcome:'delivered'|'not_sent'|'unknown',
receipt_ref}]} after actual channel lookup. Never retry on timeout alone.
Task results: {reports:[{id,claim_token,result,uncertainty:[]}]}.
Manager review/closure stays explicit through the task tools. collect returns
prepared task metadata to the host, not specialist evidence or a spawned agent.
Respect lease_until, current participant authority and channel idempotency_key.
Private job files contain data and claim tokens; remove them under the same
retention policy after processing. Stdout reports counts only.
"""
import argparse
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wellbeing.core import atomic_json, private_path, read_json
from wellbeing.database import Database
from wellbeing.service import Service


def collect(service, p):
    status = service.status(p)
    if not status['enabled']:
        return {'status': 'paused', 'tasks': [], 'deliveries': []}
    if p['role'] == 'host':
        service.tick(p['participant'])
        return {'status': 'host_action_required', 'tasks': service.tasks(p),
                'deliveries': service.claim_outbox(p),
                'contract': 'Use real host tools; uncertainty requires reconciliation; no automatic resend.'}
    claimed = service.task(p, 'claim', {})
    return {'status': 'role_execution_required', 'task': claimed,
            'instructions': 'agents/' + p['role'] + '.md',
            'execution_mode': 'host_must_record_native_or_virtual_truthfully'}


def apply_results(service, p, results):
    if not isinstance(results, dict) or set(results) - {'deliveries', 'reconciliations', 'reports'}:
        raise ValueError('Invalid host result file')
    for values in results.values():
        if not isinstance(values, list) or len(values) > 100:
            raise ValueError('Bounded result arrays required')
    counts = {'deliveries': 0, 'reconciliations': 0, 'reports': 0}
    for value in results.get('deliveries', []):
        service.acknowledge(p, value); counts['deliveries'] += 1
    for value in results.get('reconciliations', []):
        service.reconcile_delivery(p, value); counts['reconciliations'] += 1
    for value in results.get('reports', []):
        service.task(p, 'report', value); counts['reports'] += 1
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('operation', choices=('collect', 'apply'))
    parser.add_argument('--home'); parser.add_argument('--output'); parser.add_argument('--results')
    args = parser.parse_args()
    # Validate output before claiming jobs; avoid losing a claim to an invalid destination.
    if args.operation == 'collect':
        if not args.output:
            parser.error('collect requires --output outside repository')
        output = private_path(args.output)
        if output.exists() or output.is_symlink():
            raise ValueError('Choose a fresh private job path; preserve unresolved prior jobs')
    db = Database(args.home); service = Service(db)
    p = db.principal(os.environ.get('WELLBEING_ROLE_TOKEN', ''))
    if args.operation == 'collect':
        job = collect(service, p); atomic_json(output, job)
        print(json.dumps({'status': job['status'], 'private_job_written': True}))
    else:
        if not args.results:
            parser.error('apply requires --results')
        source = private_path(args.results)
        if source.is_symlink():
            raise ValueError('Refusing symlink results')
        print(json.dumps(apply_results(service, p, read_json(source))))


if __name__ == '__main__':
    main()
