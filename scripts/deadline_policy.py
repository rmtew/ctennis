"""Bind the experimental policy to the actually executed image and source."""
import json
from native_evidence import digest
from native_tools import ROOT
POLICY=ROOT/'docs/tutorial-deadline-cost-policy.json'

def record(executable):
    data=json.loads(POLICY.read_text())
    return dict(policy=data,policy_sha256=digest(POLICY),
        scheduler_source_sha256=digest(ROOT/'amiga/game/tutorial_deadline.s'),
        main_source_sha256=digest(ROOT/'amiga/main.s'),executable_sha256=digest(executable),
        tool_binding='Enclosing receipt files/tools and actual compiled manifest')
