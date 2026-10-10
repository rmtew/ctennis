"""Bound observer drain requests without changing the requested guest goal.

A provider target stop completes a drain slice, not necessarily the caller's
advance. PC stops may interrupt any slice; the next request starts there.
"""
SLICE_MILLISECONDS=1


def drain_target(current_cck,goal_cck,physical_clock):
    assert current_cck<=goal_cck and physical_clock>0
    maximum_delta=(physical_clock*SLICE_MILLISECONDS+999)//1000
    return min(goal_cck,current_cck+maximum_delta)


def goal_reached(stop,requested_cck,goal_cck):
    return stop['cck']>=goal_cck or (stop.get('reason')=='target' and requested_cck==goal_cck)
