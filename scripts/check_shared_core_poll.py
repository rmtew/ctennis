"""Replay recorded logical calls and prove extra lifecycle polls are inert."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from build_match_core import load_image
from match_core_cpu import Core
from native_tools import ROOT
from run_shared_match_core import READONLY


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    assert report['passed']
    executable = ROOT/'build/standalone/match-core'
    assert hashlib.sha256(executable.read_bytes()).hexdigest() == report['sha256'][str(executable.relative_to(ROOT))]
    image,symbols = load_image(executable)
    output = args.report.parent/'poll-idempotence.json'
    output.write_text(json.dumps({'passed':False,'state':'incomplete'})+'\n')
    transitions,counts,max_cycles = Counter(),Counter(),{}
    with Core(image,symbols,poison=0x69,readonly=READONLY) as cpu:
        for row in report['rows']:
            before = cpu.state()
            cpu.clear_events()
            cycles = cpu.call_logical(row['operation'],row['arguments'])
            assert cpu.state().hex() == row['state'], ('recorded state',row['index'])
            assert cpu.events == row['events'], ('recorded outputs',row['index'])
            max_cycles[row['operation']] = max(cycles,max_cycles.get(row['operation'],0))
            if row['operation'] == 'game_round_poll':
                first = cpu.state()
                life = int.from_bytes(first[216:218],'big')
                counts[life] += 1
                if first != before:
                    transitions[(int.from_bytes(before[216:218],'big'),life)] += 1
                for repeat in range(2):
                    cpu.clear_events()
                    cpu.call_logical('game_round_poll',[])
                    assert cpu.state() == first, ('Repeated poll changes state',row['index'],life,repeat)
                    assert cpu.events == [], ('Repeated poll emits outputs',row['index'],life,repeat,cpu.events)
            if row['index'] % 10000 == 0:
                print('Poll proof replay operation',row['index'],flush=True)
        cpu.audit_reads()
    result = {'passed':True,'capture_sha256':hashlib.sha256(args.report.read_bytes()).hexdigest(),
        'standalone_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
        'cpu_guard_sha256':hashlib.sha256((ROOT/'scripts/match_core_cpu.py').read_bytes()).hexdigest(),
        'context_guard':'Fresh D/A/CCR poison every call; declared word arguments preserve poisoned upper halves',
        'operations':len(report['rows']),'extra_polls_per_boundary':2,
        'poll_lifecycle_counts':dict(counts),
        'observed_transitions':{f'{a}->{b}':count for (a,b),count in transitions.items()},
        'max_observed_isolated_cycles_by_api':max_cycles,
        'scope':'Finite recorded domain; isolated CPU cycles do not establish contended native deadlines'}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
