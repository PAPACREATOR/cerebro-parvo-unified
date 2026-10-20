"""Synthetic lab only: Markdown objects + disposable SQLite index, no Nexus writes.

--cases counts round-trip object checks, NOT independent semantic test scenarios.
The JSON metadata comment is an experimental lab envelope, not F009's schema.
"""
import argparse
import hashlib
import json
import platform
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def encode(meta, body):
    return ('<!-- nexus-lab ' + json.dumps(meta, ensure_ascii=False, sort_keys=True)
            + ' -->\n' + body).encode('utf-8')


def decode(raw):
    header, body = raw.decode('utf-8').split('\n', 1)
    if not header.startswith('<!-- nexus-lab ') or not header.endswith(' -->'):
        raise ValueError('invalid envelope')
    meta = json.loads(header[len('<!-- nexus-lab '):-4])
    if set(meta) != {'id', 'version', 'kind', 'domain', 'origin', 'refs'}:
        raise ValueError('invalid fields')
    if meta['domain'] != 'creative' or meta['version'] != 1:
        raise ValueError('unsupported authority/version')
    if meta['kind'] not in ('source', 'note') or not isinstance(meta['refs'], list):
        raise ValueError('invalid kind/relations')
    return meta, body


def rebuild(objects, db, manifest):
    con = sqlite3.connect(db)
    try:
        con.executescript('CREATE TABLE objects(id TEXT PRIMARY KEY, path TEXT, digest TEXT);'
                          'CREATE TABLE edges(src TEXT, dst TEXT, PRIMARY KEY(src,dst));'
                          'CREATE INDEX inverse ON edges(dst);'
                          'CREATE VIRTUAL TABLE search USING fts5(id UNINDEXED, body);')
        seen = set()
        for path in objects.glob('*.md'):
            raw = path.read_bytes()
            meta, body = decode(raw)
            require(sha(raw) == manifest.get(meta['id']), 'hash mismatch')
            con.execute('INSERT INTO objects VALUES(?,?,?)', (meta['id'], path.name, sha(raw)))
            con.execute('INSERT INTO search VALUES(?,?)', (meta['id'], body))
            con.executemany('INSERT INTO edges VALUES(?,?)', [(meta['id'], r) for r in meta['refs']])
            seen.add(meta['id'])
        require(seen == set(manifest), 'missing object')
        require(con.execute('SELECT count(*) FROM edges LEFT JOIN objects ON dst=id WHERE id IS NULL').fetchone()[0] == 0, 'broken link')
        con.commit()
    finally:
        con.close()


def expect_reject(fn, expected_message):
    try:
        fn()
    except (AssertionError, ValueError, sqlite3.IntegrityError) as error:
        require(expected_message in str(error), f"wrong rejection: {error}")
        return
    raise AssertionError('invalid data accepted')


def run(cases, output):
    require(cases >= 2 and cases % 2 == 0, 'cases must be positive even number >= 2')
    output.mkdir(parents=True, exist_ok=True)
    report = {'status': 'RUNNING', 'object_cases_requested': cases, 'phases': [],
              'platform': platform.platform(), 'python': platform.python_version(),
              'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'runner_sha256': sha(Path(__file__).read_bytes()),
              'not_run': ['Windows', 'real web/AI', 'Nexus integration', 'power loss',
                          'historical version editing', 'semantic quality', 'human gate integration']}
    started = time.perf_counter()
    def phase(name, **metrics):
        report['phases'].append(dict(name=name, status='PASS', **metrics))
        print(name, 'PASS', flush=True)
    try:
        with tempfile.TemporaryDirectory(prefix='nexus-wiki-study-') as folder:
            root = Path(folder)
            objects = root / 'objects'
            objects.mkdir()
            manifest = {}
            t = time.perf_counter()
            for i in range(cases // 2):
                token = f'topic{i:06d}'
                for kind in ('source', 'note'):
                    oid = f'{kind}-{i:06d}'
                    meta = dict(id=oid, version=1, kind=kind, domain='creative',
                                origin=f'https://example.invalid/{i}' if kind == 'source' else f'run-{i:06d}',
                                refs=[] if kind == 'source' else [f'source-{i:06d}'])
                    raw = encode(meta, f'# {token}\nInvestigação sintética: ação, café, 日本語.\n{kind}\n')
                    (objects / f'{oid}.md').write_bytes(raw)
                    manifest[oid] = sha(raw)
            phase('materialize', objects=cases, seconds=time.perf_counter()-t)
            db = root / 'index.sqlite'
            t = time.perf_counter()
            rebuild(objects, db, manifest)
            phase('index', relations=cases//2, seconds=time.perf_counter()-t)
            con = sqlite3.connect(db)
            t = time.perf_counter()
            for i in range(cases//2):
                source, note = f'source-{i:06d}', f'note-{i:06d}'
                require(con.execute('SELECT dst FROM edges WHERE src=?', (note,)).fetchall() == [(source,)], 'forward mismatch')
                require(con.execute('SELECT src FROM edges WHERE dst=?', (source,)).fetchall() == [(note,)], 'reverse mismatch')
                found = {r[0] for r in con.execute('SELECT id FROM search WHERE search MATCH ?', (f'topic{i:06d}',))}
                require(found == {source, note}, 'search mismatch')
            con.close()
            phase('bidirectional_search', object_cases=cases, queries=cases//2, seconds=time.perf_counter()-t)
            # Rename changes physical path, never logical ID; full rebuild reads disk.
            (objects / 'note-000000.md').rename(objects / 'renomeado.md')
            db.unlink()
            t = time.perf_counter()
            rebuild(objects, db, manifest)
            con = sqlite3.connect(db)
            require(con.execute('SELECT path FROM objects WHERE id=?', ('note-000000',)).fetchone() == ('renomeado.md',), 'rename identity lost')
            require(con.execute('SELECT count(*) FROM objects').fetchone()[0] == cases, 'rebuild loss')
            con.close()
            phase('reopen_rebuild_rename', seconds=time.perf_counter()-t, verified_hashes=cases)
            # Independent hostile fixtures: use tiny copies; never delete originals.
            tiny = root / 'hostile'
            tiny.mkdir()
            source_raw = (objects / 'source-000000.md').read_bytes()
            note_raw = (objects / 'renomeado.md').read_bytes()
            controls = 0
            for name in ('corrupt', 'missing', 'broken', 'duplicate', 'authority', 'malformed'):
                for p in tiny.glob('*.md'):
                    p.unlink()
                (tiny / 'source.md').write_bytes(source_raw)
                (tiny / 'note.md').write_bytes(note_raw)
                expected = {k: manifest[k] for k in ('source-000000', 'note-000000')}
                if name == 'corrupt':
                    (tiny / 'note.md').write_bytes(note_raw + b'changed')
                elif name == 'missing':
                    (tiny / 'source.md').unlink()
                elif name == 'duplicate':
                    (tiny / 'copy.md').write_bytes(note_raw)
                else:
                    meta, body = decode(note_raw)
                    if name == 'broken':
                        meta['refs'] = ['absent']
                    elif name == 'authority':
                        meta['domain'] = 'canonical'
                    raw = b'bad envelope\nbody' if name == 'malformed' else encode(meta, body)
                    (tiny / 'note.md').write_bytes(raw)
                    expected['note-000000'] = sha(raw)
                messages = dict(corrupt='hash mismatch', missing='missing object', broken='broken link',
                                duplicate='UNIQUE constraint', authority='unsupported authority', malformed='invalid envelope')
                expect_reject(lambda: rebuild(tiny, root / f'{name}.sqlite', expected), messages[name])
                controls += 1
            phase('adversarial', distinct_scenarios=controls)
            # Reuse archived evidence in a NEW process, no producer callable exists here.
            code = ('import sqlite3,sys,json; c=sqlite3.connect(sys.argv[1]); '
                    'print(json.dumps(c.execute("SELECT dst FROM edges WHERE src=?", '
                    '("note-000000",)).fetchall()))')
            recovered = json.loads(subprocess.check_output([sys.executable, '-c', code, str(db)], text=True))
            require(recovered == [['source-000000']], 'new process lineage mismatch')
            phase('new_process_reuse', recovered_references=1, provider_calls=0)
            report['logical_bytes'] = dict(markdown=sum(p.stat().st_size for p in objects.glob('*.md')), index=db.stat().st_size)
            report['logical_bytes_per_object'] = sum(report['logical_bytes'].values()) / cases
            report['manifest_sha256'] = sha(json.dumps(manifest, sort_keys=True).encode())
            report['object_cases_passed'] = cases
            report['status'] = 'PASS'
    except Exception as error:
        report['status'] = 'FAIL'
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        report['elapsed_seconds'] = time.perf_counter()-started
        (output / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=int, default=100000)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.cases, args.output)
