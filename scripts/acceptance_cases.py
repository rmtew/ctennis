"""Stable finite gate cases. Unknown dependency classes fail closed to full inputs."""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Case:
    id: str
    args: tuple
    report: str | None = None
    extent: str | None = None
    category: str = 'native'

def cases():
    rows = [
        Case('host-unit', ('-m','unittest','discover','-s','tests/unit','-q'), category='host'),
        Case('assets', ('scripts/native_assets.py',), category='host'),
        Case('font', ('assets/interface/font-mac/extract.py',), category='host'),
        Case('package-before', ('scripts/build_native_adf.py','--self-test'), 'amiga/interfaces/enhanced/delivery/package-report.json','package'),
        Case('menu-cold', ('scripts/run_enhanced_menu_tests.py','--adf'),'tests/enhanced-menu-cold/report.json','menu-cold'),
        Case('inputs', ('scripts/run_native_inputs.py',),'tests/native-inputs/report.json','inputs'),
        Case('video-standard', ('scripts/run_video_standard_tests.py',),'tests/video-standard/report.json'),
        Case('startup', ('scripts/run_startup_publication_tests.py',),'tests/startup-publication/report.json'),
        Case('video-clock', ('scripts/run_native_video_clock_tests.py',),'tests/native-video-clock/report.json','video-clock'),
        Case('dma-pal', ('scripts/run_sprite_dma_tests.py','--self-test'),'tests/native-sprite-dma-pal-report.json','sprite-dma-pal'),
        Case('dma-ntsc', ('scripts/run_sprite_dma_tests.py','--ntsc','--self-test'),'tests/native-sprite-dma-ntsc-report.json','sprite-dma-ntsc'),
        Case('scoreboard', ('scripts/run_native_scoreboard_tests.py','--self-test'),'tests/native-scoreboard/report.json','scoreboard'),
    ]
    for name in ('deuce','advantage','return-deuce','advantage-game','match-award','status-2','status-3','status-4','status-5','status-6','audio-hit'):
        rows.append(Case('contract-'+name,('scripts/run_native_contracts.py','--case='+name,*(['--self-test'] if name in ('deuce','status-2','status-6','audio-hit') else [])),f'tests/native-contracts/{name}/report.json',name))
    for winner, exchanged in (('blue',False),('red',False),('blue',True),('red',True)):
        rows.append(Case('celebration-'+winner+('-exchanged' if exchanged else '-normal'),('scripts/run_celebration_tests.py','--winner='+winner,*(['--exchanged'] if exchanged else []),*(['--self-test'] if winner=='blue' and not exchanged else [])),f'tests/ct13-{winner}-'+('exchanged' if exchanged else 'normal')+'/report.json'))
    for name, flag, directory in (('demo',None,'demo-full-repeat'),('takeover','--takeover','demo-mid-takeover'),('takeover-tail','--takeover-tail','demo-tail-takeover'),('takeover-sound','--takeover-round-sound','demo-sound-takeover')):
        rows.append(Case(name,('scripts/run_demo_match_tests.py',*([flag] if flag else [])),f'tests/{directory}/report.json',name if name in ('demo','takeover') else None))
    rows += [
        Case('attract',('scripts/run_attract_cycle_tests.py',),'tests/attract-two-cycles/report.json','attract-cycles'),
        Case('feedback-one',('scripts/run_enhanced_feedback_tests.py','--mode=one','--self-test'),'tests/enhanced-feedback-one/report.json','feedback-one'),
        Case('feedback-two',('scripts/run_enhanced_feedback_tests.py','--mode=two'),'tests/enhanced-feedback-two/report.json','feedback-two'),
        Case('ordinary-one-cold',('scripts/run_ordinary_round_tests.py','--mode=one','--match','--cadence','--adf'),'tests/ct10-adf-one-cadence-enhanced-report.json','ordinary-one-cold'),
        Case('ordinary-two',('scripts/run_ordinary_round_tests.py','--mode=two','--match','--cadence'),'tests/ct09-ordinary-two-cadence-enhanced-report.json','ordinary-two'),
        Case('bank-control',('scripts/run_ordinary_round_tests.py','--mode=one','--bank-control'),'tests/ct09-published-bank-control-enhanced-report.json','bank-control'),
        Case('restart',('scripts/run_ordinary_round_tests.py','--mode=one','--match','--early-release','--audio','--self-test'),'tests/ct06-ordinary-one-early-release-enhanced-report.json','restart-audio-early'),
        Case('setup',('scripts/run_native_setup_tests.py','--self-test'),'tests/native-setup/report.json','setup-proposal'),
        Case('package-after',('scripts/build_native_adf.py','--self-test'),'amiga/interfaces/enhanced/delivery/package-report.json','package'),
        Case('metrics',('scripts/native_metrics.py','--require-runtime'),category='host'),
    ]
    assert len(rows)==41 and len({r.id for r in rows})==41
    return rows + [
        Case('history-cpu', ('scripts/run_history_proof.py',),
             'tests/history-cpu/report.json', category='host'),
        Case('history-pal', ('scripts/run_shared_match_core.py','--history','--seconds=24'),
             'tests/shared-match-core-pal-history/report.json'),
        Case('history-ntsc', ('scripts/run_shared_match_core.py','--history','--seconds=24','--ntsc'),
             'tests/shared-match-core-ntsc-history/report.json'),
        Case('preview-cpu', ('scripts/run_preview_proof.py',),
             'tests/preview-cpu/report.json', category='host'),
        Case('seek-sliced-cpu', ('scripts/run_seek_sliced_proof.py',),
             'tests/seek-sliced-cpu/report.json', category='host'),
        Case('preview-native-pal', ('scripts/run_preview_native.py',),
             'tests/preview-native-pal/report.json'),
        Case('preview-native-ntsc', ('scripts/run_preview_native.py','--ntsc'),
             'tests/preview-native-ntsc/report.json'),
        Case('tutorial-court-pal', ('scripts/run_tutorial_capture.py',),
             'tests/tutorial-court-pal/report.json'),
        Case('tutorial-court-ntsc', ('scripts/run_tutorial_capture.py','--ntsc'),
             'tests/tutorial-court-ntsc/report.json'),
    ]


def diagnostic_cases():
    """Explicitly selected probes; never expand the mandatory release catalog."""
    return [
        Case('tutorial-hotspots-pal', ('scripts/run_tutorial_hotspots.py',),
             'tests/tutorial-hotspots-pal/report.json'),
        Case('tutorial-latency-pal', ('scripts/run_tutorial_latency.py',),
             'tests/tutorial-latency-pal/report.json'),
        Case('tutorial-latency-ntsc', ('scripts/run_tutorial_latency.py','--ntsc'),
             'tests/tutorial-latency-ntsc/report.json'),
    ]
