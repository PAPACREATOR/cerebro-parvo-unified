import tempfile
import os
from nexus.adapters import ace_step
from nexus.adapters import deforium_forge


def test_ace_and_deforum_adapters():
    tmp = tempfile.mkdtemp(prefix='test-ace-def-')
    # Minimal job specs
    ace_spec = {'steps': [{'name': 'noop'}], 'meta': {'title': 'test'}}
    deforum_spec = {'prompts': ['A scene'], 'frames': 10}

    res1 = ace_step.run_ace_step(ace_spec, tmp)
    res2 = deforium_forge.render_deforum_job(deforum_spec, tmp)

    assert isinstance(res1, dict) and 'status' in res1
    assert isinstance(res2, dict) and 'status' in res2
    assert res1['status'] in ('OK', 'UNKNOWN', 'FAIL')
    assert res2['status'] in ('OK', 'UNKNOWN', 'FAIL')
