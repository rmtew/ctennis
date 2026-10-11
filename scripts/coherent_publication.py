"""Keep immutable bank proof separate from controller-clean COPJMP flags.

A queued construction flag does not make its completed bank partial. Requiring
live dirty=0 is a narrower controller-clean gate: an IRQ may publish a valid
completed bank before the producer clears that flag.
"""
from tutorial_capture import SurfaceObserver


class CoherentSurfaceObserver(SurfaceObserver):
    def snapshot(self,copper,state,position,actual=False):
        result=super().snapshot(copper,state,position,actual=actual)
        if result is not None and actual:
            result['publication_live_fields']={name:value for name,value in state.items() if name.startswith('tutorial_')}
        return result


def qualified_endpoint(scene,generation,request_cck):
    bank=scene.get('tutorial_fields',{});live=scene.get('publication_live_fields')
    if not live:return False
    return bool(scene['position']['cck']>=request_cck
        and bank.get('tutorial_generation')==generation
        and bank.get('tutorial_presentation_generation')==generation
        and bank.get('tutorial_placement_ready')
        and live.get('tutorial_generation')==generation
        and live.get('tutorial_presentation_generation')==generation
        and not live.get('tutorial_placement_dirty',1)
        and bank.get('tutorial_active_variant')==0
        and bank.get('tutorial_ball_mode') in (1,2)
        and ((scene.get('endpoint_outcomes',0)>>16) or (bank.get('tutorial_available_outcomes',0)>>16))
        and isinstance(scene.get('native_sprite_check'),dict)
        and scene['native_sprite_check'].get('matched') is True)


def early_endpoint(scene,generation,request_cck):
    return bool(qualified_endpoint(scene,generation,request_cck)
        and scene['tutorial_fields']['tutorial_ball_mode']==1
        and scene['tutorial_fields'].get('tutorial_marker_ready')
        and isinstance(scene.get('endpoint_points'),str) and len(scene['endpoint_points'])==32
        and scene['native_sprite_check'].get('actual_sample')==scene['endpoint_points'][:16]
        and scene.get('endpoint_outcomes',0)>>16
        and scene.get('endpoint_ready',0)>>8
        and scene.get('endpoint_generation')==generation
        and not (scene['tutorial_fields'].get('tutorial_available_outcomes',0)>>16))
