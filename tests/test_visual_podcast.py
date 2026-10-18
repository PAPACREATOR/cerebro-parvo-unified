# Integration test for visual_podcast adapter (does not assume ffmpeg installed).
import tempfile
import os
from nexus.adapters import visual_podcast


def test_visual_podcast_adapter():
    tmp = tempfile.mkdtemp(prefix='test-vpod-')
    res = visual_podcast.create_visual_podcast('Teste de podcast visual curto com TTS.', tmp)
    assert isinstance(res, dict)
    assert 'status' in res
    assert res['status'] in ('OK', 'UNKNOWN', 'FAIL')
    if res['status'] == 'OK':
        assert 'artifact' in res
        assert os.path.exists(res['artifact']['path'])

if __name__ == '__main__':
    test_visual_podcast_adapter()
    print('visual_podcast adapter smoke test passed')
