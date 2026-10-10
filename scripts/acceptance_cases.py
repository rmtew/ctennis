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
        Case('coherent-contact-pal', ('scripts/run_physics_contact_native.py','--coherent'), 'tests/coherent-contact-native-pal/report.json'),
        Case('coherent-contact-ntsc', ('scripts/run_physics_contact_native.py','--coherent','--ntsc'), 'tests/coherent-contact-native-ntsc/report.json'),
        Case('physics-contact-pal', ('scripts/run_physics_contact_native.py',), 'tests/physics-contact-native-pal/report.json'),
        Case('physics-contact-ntsc', ('scripts/run_physics_contact_native.py','--ntsc'), 'tests/physics-contact-native-ntsc/report.json'),
        Case('physics-cpu', ('scripts/run_physics_proof.py',), 'tests/physics-cpu/report.json', category='host'),
        Case('physics-control-pal', ('scripts/run_incoming_native.py','--physics','--physics-control'), 'tests/physics-control-native-pal/report.json'),
        Case('physics-pal', ('scripts/run_incoming_native.py','--physics'), 'tests/physics-native-pal/report.json'),
        Case('physics-control-ntsc', ('scripts/run_incoming_native.py','--physics','--physics-control','--ntsc'), 'tests/physics-control-native-ntsc/report.json'),
        Case('physics-ntsc', ('scripts/run_incoming_native.py','--physics','--ntsc'), 'tests/physics-native-ntsc/report.json'),
        Case('deadline-class-cpu', ('scripts/run_deadline_class_proof.py',), 'tests/deadline-class-cpu/report.json', category='host'),
        Case('deadline-pal', ('scripts/run_incoming_native.py','--deadline'), 'tests/deadline-native-pal/report.json'),
        Case('deadline-ntsc', ('scripts/run_incoming_native.py','--deadline','--ntsc'), 'tests/deadline-native-ntsc/report.json'),
        Case('incoming-origin-cpu', ('scripts/run_incoming_origin_proof.py',), 'tests/incoming-origin-cpu/report.json', category='host'),
        Case('incoming-origin-pal', ('scripts/run_incoming_native.py','--origin-cache'), 'tests/incoming-origin-native-pal/report.json'),
        Case('incoming-origin-ntsc', ('scripts/run_incoming_native.py','--origin-cache','--ntsc'), 'tests/incoming-origin-native-ntsc/report.json'),
        Case('predictor-boundaries-cpu', ('scripts/run_predictor_boundaries.py',),
             'tests/predictor-boundaries-cpu/report.json', category='host'),
        Case('predictor-cpu', ('scripts/run_predictor_proof.py',),
             'tests/predictor-cpu/report.json', category='host'),
        Case('predictor-pal', ('scripts/run_incoming_native.py','--predictor'),
             'tests/predictor-native-pal/report.json'),
        Case('predictor-ntsc', ('scripts/run_incoming_native.py','--predictor','--ntsc'),
             'tests/predictor-native-ntsc/report.json'),
        Case('incoming-flight-cpu', ('scripts/run_incoming_proof.py',),
             'tests/incoming-flight-cpu/report.json', category='host'),
        Case('incoming-flight-pal', ('scripts/run_incoming_native.py',),
             'tests/incoming-flight-native-pal/report.json'),
        Case('incoming-flight-ntsc', ('scripts/run_incoming_native.py','--ntsc'),
             'tests/incoming-flight-native-ntsc/report.json'),
        Case('guarded-landing-cpu', ('scripts/run_landing_proof.py',),
             'tests/guarded-landing-cpu/report.json', category='host'),
        Case('guarded-landing-pal', ('scripts/run_landing_native.py',),
             'tests/guarded-landing-native-pal/report.json'),
        Case('guarded-landing-ntsc', ('scripts/run_landing_native.py','--ntsc'),
             'tests/guarded-landing-native-ntsc/report.json'),
        Case('ratio32-cpu', ('scripts/run_ratio32_proof.py',),
             'tests/ratio32-cpu/report.json', category='host'),
        Case('ratio32-live-baseline-pal', ('scripts/run_ratio32_native.py','--variant=baseline'),
             'tests/ratio32-live-baseline-pal/report.json'),
        Case('ratio32-live-baseline-ntsc', ('scripts/run_ratio32_native.py','--variant=baseline','--ntsc'),
             'tests/ratio32-live-baseline-ntsc/report.json'),
        Case('ratio32-live-candidate-pal', ('scripts/run_ratio32_native.py','--variant=candidate'),
             'tests/ratio32-live-candidate-pal/report.json'),
        Case('ratio32-live-candidate-ntsc', ('scripts/run_ratio32_native.py','--variant=candidate','--ntsc'),
             'tests/ratio32-live-candidate-ntsc/report.json'),
        Case('private-state-retained-pal', ('scripts/run_retained_private_native.py',),
             'tests/private-state-retained-pal/report.json'),
        Case('private-state-retained-ntsc', ('scripts/run_retained_private_native.py','--ntsc'),
             'tests/private-state-retained-ntsc/report.json'),
        Case('private-state-cpu', ('scripts/run_private_state_proof.py',),
             'tests/private-state-cpu/report.json', category='host'),
        Case('tutorial-hotspots-pal', ('scripts/run_tutorial_hotspots.py',),
             'tests/tutorial-hotspots-pal/report.json'),
        Case('tutorial-latency-pal', ('scripts/run_tutorial_latency.py',),
             'tests/tutorial-latency-pal/report.json'),
        Case('tutorial-latency-ntsc', ('scripts/run_tutorial_latency.py','--ntsc'),
             'tests/tutorial-latency-ntsc/report.json'),
    ]
