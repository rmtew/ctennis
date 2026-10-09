"""Fail-closed selective predictor evidence extent; never a release gate."""
import json
import gzip
from native_evidence import digest
from native_tools import ROOT


def cpu_extent(report):
    v=report.get('validation') or {};rows=v.get('rows') or [];apis=v.get('api_cases') or []
    guards=v.get('guard_cases') or [];irregular=v.get('irregular_cases') or []
    original=v.get('original_core_bytes') or {};predictor=v.get('predictor_bytes') or {}
    return (report.get('execution')=='actual-68000-cpu-only' and v.get('passed') is True
        and v.get('full_private_bytes')==318 and v.get('added_metadata_bytes')==6
        and len(rows)==56 and len(apis)==16 and len(guards)==26 and len(irregular)==2
        and len({(r.get('seed'),r.get('end'),r.get('x'),r.get('y'),r.get('held'),r.get('poison')) for r in rows})==56
        and {(r.get('seed'),r.get('end'),r.get('budget')) for r in apis}==
            {(seed,end,budget) for seed,end in ((1,0),(0xace1,0),(0xbeef,0),(0xace1,1)) for budget in (1,2,3,4)}
        and {r.get('name') for r in guards}=={'exact-policy','serve-kind','invalid-kind','missing-incoming',
            'lifecycle','uninitialized','idle-stage','invalid-stage','pending-command','restart','suppressed-input',
            'round-mode','result-mode','two-human-mode','invalid-end','scorer-ai','score-flags','end-mode',
            'human-ai','opponent-human','owner','upper-owner','wrong-side','terminal','launch-pending','no-flight'}
        and all(r.get('passed') is True for r in rows+apis+guards+irregular)
        and {r.get('seed') for r in rows}=={1,0xace1,0xbeef}
        and {r.get('budget') for r in apis}=={1,2,3,4}
        and {r.get('reason') for r in guards}==set(range(1,8))
        and all(r.get('registers_preserved') is True and r.get('admission_read_only') is True for r in guards)
        and all(r.get('full_state_events_equal') is True for r in guards if r.get('scope')=='full-fallback')
        and all(not r.get('omitted_reads') and r.get('retained_bytes')==210 for r in rows)
        and any(r.get('natural_exchange') is True for r in rows)
        and any(r.get('low_height_contact') is True for r in rows)
        and any(r.get('wide') for r in rows) and any(r.get('handoffs') for r in rows)
        and {'landing','net','no-contact'}<={r.get('termination') for r in rows}
        and all(r.get('stale_cancel_neutral') is True and r.get('populated_history_isolated') is True
            and any(s.get('api')=='active-projected-to-exact' and s.get('completed') is True
                and s.get('exact_full_state_events_equal') is True for s in r.get('policy_switches') or []) for r in apis)
        and all(r.get('required_observations_cursors_equal') is True for r in irregular)
        and original.get('passed') is True and original.get('matched_bytes')==17606
        and original.get('normalized_sha256')=='99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5'
        and predictor.get('passed') is True and isinstance(predictor.get('bytes'),int) and predictor['bytes']>0)


def native_extent(report,standard,prefix='predictor-native-'):
    relative='build/tests/'+prefix+standard.lower()+('/latency.json.gz' if prefix=='incoming-origin-native-' else '/latency.json')
    files=(report.get('evidence') or {}).get('files') or {}
    if report.get('capture')!=relative or files.get(relative)!=digest(ROOT/relative):return False
    try:
        with (gzip.open(ROOT/relative,'rt') if relative.endswith('.gz') else (ROOT/relative).open()) as handle:captured=json.load(handle)
    except (OSError,ValueError):return False
    rows=report.get('endpoints') or [];probe=report.get('input_probe') or {}
    timing=report.get('timing') or {};resume=report.get('resume_latest') or {}
    return (report.get('guarded_predictor') is True and report.get('emitted_kernel_calls',0)>0
        and report.get('cancelled_active_job') is True and report.get('record_store_unchanged') is True
        and report.get('first_resumed_boundary_equal') is True
        and resume.get('passed') is True and resume.get('state')==resume.get('expected')
        and resume.get('history')==resume.get('expected_history') and resume==captured.get('resume_latest')
        and probe.get('passed') is True and probe==captured.get('input_probe')
        and probe.get('minimum_ack_hold_cck',0)>=350 and probe.get('maximum_keyboard_poll_gap_cck',0)>0
        and len(probe.get('transitions') or [])>=16
        and timing.get('minimum_absolute_headroom_cck',0)>0
        and rows==captured.get('endpoints') and len(rows) in (2,3)
        and all(r.get('routes')==[1,1] and r.get('guard_reason')==0
            and (r.get('original_incoming_reference') or {}).get('passed') is True
            and (r.get('original_incoming_reference') or {}).get('path_prefix_equal') is True for r in rows)
        and all((r.get('contact_timing') or {}).get('accepted_hook_to_dispatch_return_cck',-1)>=0
            and (r.get('contact_timing') or {}).get('dispatch_return_to_copjmp_cck',-1)>=0
            for r in rows if (r.get('human_launches') or [0])[0]))
