"""Finite actual footer step observations; no CPU or DMA safety model."""

def validate_stages(c, owners):
    calls = c['stack_timing']['calls']
    emitted = {i for i, row in enumerate(calls) if row['callee'] == 'tutorial_footer_step'}
    seen, results = set(), []
    for row in c['footer_stage_profiles']:
        matches = [i for i in emitted if calls[i]['entry']['cck'] <= row['entry']['cck']
                   <= calls[i]['exit']['cck'] <= row['exit']['cck']]
        assert len(matches) == 1 and matches[0] not in seen, 'Footer stage profile lacks unique call'
        index = matches[0]; seen.add(index); call = calls[index]
        assert any(owner['entry']['cck'] <= call['entry']['cck'] <= call['exit']['cck'] <= row['exit']['cck'] <= owner['exit']['cck'] for _, owner in owners), 'Footer stage outside root owner'
        glyphs=[r for r in calls if r['callee']=='ui_text_character' and call['entry']['cck']<=r['entry']['cck']<=r['exit']['cck']<=call['exit']['cck']]
        assert len(glyphs)<=2,'Footer stage exceeds two actual glyph calls'
        before, after = row['before'], row['after']
        assert before['overlay'] == after['overlay'], 'Private footer step changed live overlay'
        assert row['completed'] in (0, 1), 'Invalid footer completion result'
        assert after['ready'] == 0, 'Footer step prematurely marked ready'
        if row['completed']:
            assert after['stage'] == 0 and after['first'] and after['second'], 'Completed footer lacks completed cache'
        else:
            assert after['stage'] in (1, 2) and after['first'] == after['second'] == 0, 'Partial footer has completed cache'
            assert after['stage_generation'] == after['generation'], 'Partial footer belongs to stale generation'
        results.append(dict(call_index=index, elapsed_bus_cck=call['elapsed_bus_cck'], glyph_calls=len(glyphs), completed=bool(row['completed']), stage_before=before['stage'], stage_after=after['stage'], generation=after['generation']))
    assert seen == emitted, 'Footer stage profiles do not cover every emitted call'
    return results


def validate_final_caption(c, commits):
    """Bind the stable final observation to actual stage, copy and readback."""
    w=c['final_caption'];generation=c['endpoints'][-1]['generation']
    assert w['generation']==generation and len(c['endpoints'])==9,'Final caption does not belong to ninth endpoint'
    assert w['limit_seconds']==2 and w['physical_clock_hz'] in (3546895,3579545),'Final caption settle bound changed'
    assert w['elapsed_cck']==w['observed']['cck']-w['start']['cck'] and 0<=w['elapsed_cck']<=2*w['physical_clock_hz'],'Final caption exceeded stable settle bound'
    completion=w['completion'];state=completion['state']
    assert sum(r==completion for r in c['footer_commit_completions'])==1,'Final caption lacks unique actual commit completion'
    matches=[r for r in commits if r['entry']['cck']<=completion['entry']['cck']<=r['exit']['cck']<=completion['position']['cck']]
    assert len(matches)==1 and matches[0]['bytes_written']==512,'Final caption lacks actual live512 copy'
    commit=matches[0]
    assert commit['generation']==commit['footer_generation']==generation,'Final caption copied stale generation'
    assert state==w['final_state'],'Final observed caption differs from committed readback'
    assert state['generation']==state['footer_generation']==state['stage_generation']==generation,'Final caption metadata belongs to stale generation'
    assert state['dirty']==state['ready']==state['stage']==0 and state['first'] and state['second'],'Final caption remains partial or pending'
    assert len(bytes.fromhex(state['overlay']))==512 and state['overlay']==state['scratch'],'Final live overlay differs from completed caption'
    assert w['final_input_request']==c['endpoints'][-1]['request'],'Final caption request differs from ninth input'
    assert w['caption_commit_latency_cck']==completion['position']['cck']-w['final_input_request']['cck']>=0,'Final caption latency does not bind actual copy return'
    assert w['final_input_request']['cck']<=completion['position']['cck']<=w['observed']['cck'],'Final caption completion outside measured interval'
    profiles=[r for r in c['footer_stage_profiles'] if r['completed']==1 and r['exit']['cck']<=completion['entry']['cck'] and r['after']['generation']==generation and r['after']['first']==state['first'] and r['after']['second']==state['second'] and r['after']['scratch']==state['scratch']]
    assert profiles,'Final live caption lacks completed actual stage metadata'
    assert any(r['entry']['cck']<=commit['entry']['cck']<=commit['exit']['cck']<=completion['position']['cck']<=r['exit']['cck'] for r in c['stack_timing']['calls'] if r['callee']=='tutorial_background'),'Final commit return tail outside root owner'
    return dict(passed=True,generation=generation,bytes_committed=512,settle_elapsed_cck=w['elapsed_cck'],caption_commit_latency_cck=w['caption_commit_latency_cck'],commit_entry=commit['entry'],commit_exit=commit['exit'],commit_readback=completion['position'],scope='Finite stable final caption commit/readback; no first-scanout witness. Endpoint latencies unchanged')
