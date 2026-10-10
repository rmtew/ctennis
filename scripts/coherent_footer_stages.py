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
