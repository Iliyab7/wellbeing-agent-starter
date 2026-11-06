#!/usr/bin/env python3
"""Exercise the actual CLI with synthetic data in a temporary private workspace."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]


def run(keep=False):
    directory = Path(tempfile.mkdtemp(prefix='wellbeing-synthetic-'))
    home = directory / 'participant'
    results = []
    def command(*args, expected=0):
        result = subprocess.run([sys.executable, '-m', 'wellbeing', '--home', str(home), *args],
                                cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != expected:
            raise RuntimeError(f'CLI {args[0]} failed unexpectedly: {result.stderr}')
        payload = json.loads(result.stdout if expected == 0 else result.stderr)
        results.append({'command': args[0], 'expected_exit': expected, 'passed': True})
        return payload.get('result', payload)
    try:
        command('init', '--goal', 'Synthetic: understand my recorded energy', '--timezone', 'UTC')
        command('import', '--file', str(directory/'missing.json'), expected=2)
        command('configure', '--file', str(ROOT/'examples/policy.synthetic.json'), '--confirmed',
                '--consent-reference', 'synthetic test only; not participant consent')
        now = datetime.now(timezone.utc)
        records = [{'id':f'synthetic-{n}', 'source':'manual', 'metric':'sleep_hours', 'value':v,
                    'unit':'hours', 'observed_at':(now-timedelta(days=6-n, minutes=5)).isoformat(),
                    'origin':'synthetic'} for n,v in enumerate([7,6.5,None,7.5,6,7,7.25])]
        file = directory/'records.json'
        file.write_text(json.dumps(records), encoding='utf-8')
        imported=command('import', '--file', str(file))
        assert imported['added']==7
        duplicate=command('import', '--file', str(file))
        assert duplicate['duplicates_skipped']==7
        observed=command('analyze', '--source','manual','--metric','sleep_hours')
        assert observed['observations']['numeric_count']==6
        assert observed['observations']['explicit_missing_count']==1
        assert observed['observations']['mean_of_recorded_values']==6.875
        manifest=command('team','--mode','native')
        assert manifest['execution_status']=='manifest_only'
        assert all(member['skills'] for member in manifest['members'])
        contract=json.loads((ROOT/'examples/task.synthetic.json').read_text(encoding='utf-8'))
        contract_file=directory/'task.json'
        contract_file.write_text(json.dumps(contract),encoding='utf-8')
        task=command('task','create','--file',str(contract_file))
        assert task['status']=='prepared'
        context=command('task','context','--id',task['id'])
        assert [row['id'] for row in context['evidence']]==['synthetic-0']
        assert context['skills'] and context['receipt']=='prepared_not_sent'
        command('task','dispatch-unknown','--id',task['id'],'--receipt-ref','synthetic attempt fixture')
        command('task','dispatch','--id',task['id'],'--receipt-ref','synthetic unsafe retry',expected=2)
        command('task','reconcile','--id',task['id'],'--outcome','not_sent','--receipt-ref','synthetic no-send receipt')
        command('task','dispatch','--id',task['id'],'--receipt-ref','synthetic dispatch fixture; no live agent')
        report=json.loads((ROOT/'examples/task-report.synthetic.json').read_text(encoding='utf-8'))
        report_file=directory/'report.json'
        report_file.write_text(json.dumps(report),encoding='utf-8')
        received=command('task','report','--id',task['id'],'--file',str(report_file))
        assert received['status']=='report_received'
        command('task','report','--id',task['id'],'--file',str(report_file))
        command('task','review','--id',task['id'],'--decision','revise','--reason','Synthetic review asks for clearer uncertainty')
        report['result']='Synthetic revised result: one selected observation is not a trend.'
        report_file.write_text(json.dumps(report),encoding='utf-8')
        command('task','report','--id',task['id'],'--file',str(report_file))
        reviewed_task=command('task','review','--id',task['id'],'--decision','accept','--reason','Synthetic acceptance checks reviewed')
        assert reviewed_task['status']=='verified'
        closed=command('task','close','--id',task['id'],'--reason','Synthetic internal work complete; no human delivery inferred')
        assert closed['status']=='closed'
        packet_file=directory/'packet.json'
        packet=command('packet','--role','analyst','--task','Review uncertainty in this synthetic summary',
                       '--source','manual','--metric','sleep_hours','--output',str(packet_file))
        assert packet['receipt']=='prepared_not_sent'
        command('verify-packet','--file',str(packet_file))
        plan=command('plan','--text','Synthetic participant-selected experiment: record one observation tomorrow',
                     '--evidence','synthetic-0')
        reviewed=command('review','--plan-id',plan['id'],'--receipt','withheld',
                         '--outcome','Synthetic self-report: felt better')
        assert reviewed['implementation']=='unknown'
        assert reviewed['outcome']['causality']=='not_established'
        command('check-in','--text','Synthetic context only; not real health data')
        command('pause')
        command('analyze','--source','manual','--metric','sleep_hours',expected=2)
        command('configure','--file',str(ROOT/'examples/policy.synthetic.json'),'--confirmed')
        assert command('status')['status']=='paused'
        command('resume','--confirmed')
        command('verify-packet','--file',str(packet_file),expected=2)
        corrected=dict(records[0],value=7.5)
        correction_file=directory/'correction.json'
        correction_file.write_text(json.dumps(corrected),encoding='utf-8')
        corrected_result=command('correct','--file',str(correction_file),'--confirmed')
        assert corrected_result['plans_paused_for_review']==1
        historical=command('task','show','--id',task['id'])
        assert historical['status']=='closed' and historical['data_valid'] is False
        command('revoke','--source','manual')
        command('analyze','--source','manual','--metric','sleep_hours',expected=2)
        command('export','--file',str(directory/'private-export.json'),'--confirmed')
        command('delete','--confirmed')
        command('status',expected=2)
        return {'synthetic_only': True, 'network_calls': 0, 'commands_passed':len(results),
                'results':results, 'live_host_agents_tested':False,
                'workspace':str(directory) if keep else 'temporary; removed after test'}
    finally:
        if not keep:
            shutil.rmtree(directory)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keep',action='store_true',help='Keep synthetic files outside the checkout for debugging')
    args=parser.parse_args()
    print(json.dumps(run(args.keep),indent=2))
