"""Preserve every byte/path check when hashing the Writer runtime concurrently."""
import hashlib
import os
from pathlib import Path
import pytest
from nexus.adapters import writer_sandy as writer
from nexus.contracts import Blocked

def reference_identity(root):
    h = hashlib.sha256(); count = 0
    for path in sorted(root.rglob('*')):
        if path.is_file():
            h.update(str(path.relative_to(root)).replace('\\', '/').encode('utf-8'))
            h.update(b'\0'); h.update(hashlib.sha256(path.read_bytes()).digest()); count += 1
    return count, h.hexdigest()

def test_same_identity_and_detect_content_path_and_file_changes(tmp_path):
    (tmp_path/'program').mkdir();(tmp_path/'empty').mkdir()
    (tmp_path/'program/a.dll').write_bytes(b'\x00original\xff')
    (tmp_path/'z.ini').write_bytes(b'configuration')
    original = writer._tree_identity(tmp_path)
    assert original == reference_identity(tmp_path)
    (tmp_path/'program/a.dll').write_bytes(b'\x00tampered\xff')
    assert writer._tree_identity(tmp_path) != original
    (tmp_path/'program/a.dll').write_bytes(b'\x00original\xff')
    (tmp_path/'z.ini').rename(tmp_path/'other.ini')
    assert writer._tree_identity(tmp_path) != original
    (tmp_path/'other.ini').rename(tmp_path/'z.ini')
    (tmp_path/'additional').write_bytes(b'')
    assert writer._tree_identity(tmp_path) != original
    assert writer._tree_identity(tmp_path) == reference_identity(tmp_path)

def test_empty_tree_identity(tmp_path):
    assert writer._tree_identity(tmp_path) == (0, hashlib.sha256().hexdigest())

def test_read_failure_cannot_produce_an_identity(tmp_path, monkeypatch):
    (tmp_path/'a').write_bytes(b'content')
    def unavailable(_path): raise PermissionError('unavailable')
    monkeypatch.setattr(writer, 'digest_file', unavailable)
    with pytest.raises(PermissionError): writer._tree_identity(tmp_path)

def test_redirect_is_rejected_before_hashing(tmp_path, monkeypatch):
    item = tmp_path/'redirect'; item.write_bytes(b'content')
    monkeypatch.setattr(Path, 'is_junction', lambda path: path == item)
    def unexpected(_path): pytest.fail('Redirected tree must not be hashed')
    monkeypatch.setattr(writer, 'digest_file', unexpected)
    with pytest.raises(Blocked): writer._tree_identity(tmp_path)


def test_copy_preserves_every_file_empty_directory_and_mtime(tmp_path):
    source = tmp_path / 'source'; source.mkdir()
    (source / 'empty').mkdir()
    (source / 'program').mkdir()
    for index in range(80):
        item = source / 'program' / str(index)
        item.write_bytes(bytes([index]) * (index + 1))
        os.utime(item, ns=(1_700_000_000_000_000_000,) * 2)
    target = tmp_path / 'target'
    writer._copy_runtime(source, target)
    assert writer._tree_identity(source) == writer._tree_identity(target)
    assert (target / 'empty').is_dir()
    for item in source.rglob('*'):
        copied = target / item.relative_to(source)
        assert item.stat().st_mtime_ns == copied.stat().st_mtime_ns


def test_copy_failure_propagates_before_runtime_can_be_used(tmp_path, monkeypatch):
    source = tmp_path / 'source'; source.mkdir()
    (source / 'a').write_bytes(b'content')
    def denied(*args): raise PermissionError('copy unavailable')
    monkeypatch.setattr(writer.shutil, 'copy2', denied)
    with pytest.raises(PermissionError): writer._copy_runtime(source, tmp_path / 'target')


def test_copy_rejects_nested_redirect(tmp_path, monkeypatch):
    source = tmp_path / 'source'; source.mkdir()
    item = source / 'redirect'; item.mkdir()
    monkeypatch.setattr(Path, 'is_junction', lambda path: path == item)
    with pytest.raises(Blocked): writer._copy_runtime(source, tmp_path / 'target')
