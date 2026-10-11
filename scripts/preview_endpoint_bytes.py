"""Normalize only named external operands in the shared endpoint API module."""
import hashlib
from check_shared_core_bytes import normalized

EXTERNALS=('game_preview_variant','game_preview_launches','game_preview_launch_saved',
    'game_preview_launch_states','game_history_copy_state','game_preview_generation',
    'game_preview_active','game_history_seek_status','game_preview_status','game_preview_selection_valid',
    'game_preview_endpoint_attempted','game_preview_endpoint_ready','game_preview_outcomes',
    'game_preview_flight_phases','game_preview_endpoint_scratch','landing_try_fast',
    'game_preview_endpoint_reasons','game_preview_endpoint_phases','game_preview_endpoint_outcomes',
    'game_preview_endpoints','game_preview_write_point')


def audit(standalone,native):
    options=dict(begin_name='game_preview_endpoint_code_begin',end_name='game_preview_endpoint_code_end',
                 external_names=EXTERNALS)
    left=normalized(standalone,standalone.parent/'match-core.lst',**options)
    right=normalized(native,native.parent/'native.lst',**options)
    assert left==right, 'Standalone and shipping endpoint module differ'
    return dict(passed=True,matched_bytes=len(left[0]),relocations_each=left[1],
                external_branches_each=left[2],normalized_sha256=hashlib.sha256(left[0]).hexdigest())
