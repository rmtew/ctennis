"""Focused emitted-code proof of the rolling-seed R32 form; no runtime edit."""
import json
import time
from pathlib import Path
from prove_ball_queries import ROOT, HEAD, IMAGE_SHA, Core, READONLY, load_image, digest, signed_y
from prove_ball_query_forms import smear, trunc32


def seeded32(product):
    n = product >> 5
    if n < 256:
        return n
    w = n - 256
    runs = w & (w >> 1) & (w >> 2)
    return (n | ~smear(runs)) & 255


def run():
    started = time.monotonic()
    image_path = ROOT / 'build/standalone/match-core'
    assert digest(image_path) == IMAGE_SHA
    dependencies = {
        'scripts/prove_ball_queries.py': 'ac8e059decbf2f03923d0895dad6a2ca0c153190a13bc2d2a06122f1c6eb5705',
        'scripts/prove_ball_query_forms.py': 'c36eb45c16b1518fe1c892f2c9aee28414b4edd41cf0f2e46590e2cfa13f6a34',
    }
    for path, expected in dependencies.items():
        assert digest(ROOT / path) == expected
    image, symbols = load_image(image_path)
    with Core(image, symbols, readonly=READONLY) as core:
        core.cpu.set_instr_hook_callback(None)
        core.mem.set_trace_mode(False)
        assert bytes(core.mem.r_block(symbols['game_ratio'], 24)).hex() == '0280000000ff0281000000ff0282000000ffc0c176007807'
        symbols['proof_ratio_suffix'] = symbols['game_ratio'] + 24
        for p in range(65536):
            core.call('proof_ratio_suffix', {0: p, 2: 32, 3: 0, 4: 7})
            assert core.cpu.r_reg(0) == seeded32(p), p
        for a in range(256):
            for b in range(256):
                core.call('game_ratio', {0: 0x965aa500 | a, 1: 0xa5695a00 | b, 2: 0xffff0020})
                assert core.cpu.r_reg(0) == seeded32(a * b), (a, b)
    checked = 0
    for vy in range(256):
        if vy == 128:
            continue
        v = signed_y(vy)
        for n in range(256):
            if abs(v) * n >= 8192:
                continue
            r = (abs(v) * n) % 32
            for z in range(256):
                a = v + 2 * n - z
                if abs(a) > 255 or abs(a) * n >= 8192:
                    continue
                f = 2 * n * n - z * n
                e = trunc32(a * n) - trunc32(v * n)
                # Both predicates are monotone in H; their truth sets agree
                # for all H=0..255 iff the clamped number of true H agrees.
                actual_true = max(0, min(256, e))
                if v >= 0:
                    predicted_true = 0 if a < 0 else max(0, min(256, (f + r) // 32))
                elif a < 0:
                    predicted_true = max(0, min(256, (f - r - 1) // 32 + 1))
                else:
                    predicted_true = max(0, min(256, (f - r) // 32))
                assert actual_true == predicted_true, (vy, n, z, e, f, r)
                checked += 1
    assert digest(image_path) == IMAGE_SHA
    report = dict(passed=True, base_head=HEAD, image_sha256=IMAGE_SHA,
        source_sha256=digest(Path(__file__)), production_unchanged=True,
        dependencies=dependencies,
        emitted_word_products=65536, emitted_full_byte_factor_pairs=65536,
        signed_landing_parameter_triples=checked,
        all_initial_heights_0_to_255_by_monotone_truth_set=True,
        scope='Exact R32 result and guarded ordinary signed landing predicate; not native timing or full-match acceleration',
        elapsed_host_seconds=time.monotonic()-started)
    output = ROOT / 'build/tests/ball-query-math/seed-report.json'
    output.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(passed=True, report=str(output))), flush=True)


if __name__ == '__main__':
    run()
