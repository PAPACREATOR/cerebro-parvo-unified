"""Experimental read-only Store bridge. Not registered in production Host/policy."""
import os
import sqlite3
import tempfile
import uuid
from contextlib import closing
from pathlib import Path

from nexus.contracts import Blocked, strict_json, validate
from nexus.store import atomic
from nexus.lab.wiki.context_packet import check_packet, digest, raw_json, summarize


class WikiBridge:
    def __init__(self, store, lab_root):
        self.store = store  # Already initialized and owned by Kernel, not by a flow.
        self.root = Path(lab_root).resolve()
        if self.root.is_relative_to(store.root) or store.root.is_relative_to(self.root):
            raise Blocked('Laboratório deve estar separado do Store.')
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / 'wiki.sqlite'

    def snapshot(self, run_id, include_creative=False):
        with self.store.lock:
            state = self.store.state(run_id)
            if state['status'] == 'PASS':
                self.store.check_commit(state)
                authority = 'canonical'
            elif state['status'] == 'HUMAN_REQUIRED' and include_creative:
                self.store.check_candidate(state)
                authority = 'creative'
            else:
                raise Blocked('Estado ou autoridade fora do contexto permitido.')
            content = self.store.checked_bytes(authority, run_id, 'content.md')
            provenance = self.store.checked_bytes(authority, run_id, 'provenance.json')
            return dict(run_id=run_id, content_sha256=digest(content),
                        provenance_sha256=digest(provenance), authority=authority,
                        content=content.decode('utf-8'), process_id=state['process_id'],
                        input_sha256=state['input_sha256'])

    def rebuild(self):
        fd, name = tempfile.mkstemp(dir=self.root, suffix='.sqlite')
        os.close(fd)
        rejected = []
        count = 0
        try:
            with closing(sqlite3.connect(name)) as con:
                con.execute('CREATE VIRTUAL TABLE docs USING fts5(run_id UNINDEXED, hash UNINDEXED, body)')
                for path in sorted((self.store.root / 'runs').glob('*/state.json')):
                    try:
                        item = self.snapshot(path.parent.name, include_creative=True)
                    except (Blocked, OSError, KeyError, TypeError):
                        rejected.append(path.parent.name)
                        continue
                    con.execute('INSERT INTO docs VALUES(?,?,?)', (item['run_id'], item['content_sha256'], item['content']))
                    count += 1
                con.commit()
            os.replace(name, self.index)
        finally:
            Path(name).unlink(missing_ok=True)
        return dict(indexed=count, rejected=rejected)

    def search(self, query, allowed_ids, include_creative=False, limit=8):
        if not isinstance(query, str) or not query.strip() or len(query) > 200 or '\x00' in query:
            raise Blocked('Consulta inválida.')
        if not isinstance(allowed_ids, (list, tuple, set)) or not allowed_ids or len(allowed_ids) > 10000:
            raise Blocked('Escopo explícito obrigatório.')
        for run_id in allowed_ids:
            self.store.path('runs', run_id)  # ID syntax and containment; no caller paths.
        if type(limit) is not int or not 1 <= limit <= 8 or type(include_creative) is not bool:
            raise Blocked('Limites inválidos.')
        if not self.index.is_file() or self.index.is_symlink():
            raise Blocked('Índice indisponível; reconstruir.')
        found = []
        allowed = set(allowed_ids)
        with closing(sqlite3.connect(self.index)) as con:
            rows = con.execute('SELECT run_id,hash FROM docs WHERE docs MATCH ? ORDER BY run_id',
                               ('"' + query.replace('"', '""') + '"',))
            for run_id, expected_hash in rows:
                if run_id not in allowed:
                    continue
                try:
                    item = self.snapshot(run_id, include_creative)
                except Blocked:
                    # Creative exclusion is expected; corrupt/stale allowed sources block.
                    if self.store.state(run_id)['status'] == 'HUMAN_REQUIRED' and not include_creative:
                        continue
                    raise
                if item['content_sha256'] != expected_hash:
                    raise Blocked('Índice desatualizado.')
                found.append(item)
                if len(found) == limit:
                    break
        return found

    def prepare(self, objective, run_ids, include_creative=False):
        if not isinstance(run_ids, list) or not 1 <= len(run_ids) <= 8:
            raise Blocked('Seleção inválida.')
        for run_id in run_ids:
            self.store.path('runs', run_id)
        if len(set(run_ids)) != len(run_ids):
            raise Blocked('Seleção inválida.')
        if type(include_creative) is not bool:
            raise Blocked('Autoridade inválida.')
        packet = dict(version=1, objective=objective, trust='UNTRUSTED_CONTEXT',
                      sources=[self.snapshot(r, include_creative) for r in run_ids])
        try:
            return check_packet(packet)
        except ValueError as error:
            raise Blocked(str(error)) from error

    def revalidate(self, packet):
        check_packet(packet)
        for source in packet['sources']:
            current = self.snapshot(source['run_id'], source['authority'] == 'creative')
            if current != source:
                raise Blocked('Referência mudou após seleção; preparar contexto novamente.')

    def save_experiment(self, packet, response):
        self.revalidate(packet)
        if not isinstance(response, dict) or set(response) != {'result', 'trace'} or not isinstance(response['trace'], dict):
            raise Blocked('Envelope experimental inválido.')
        validate('result', response['result'])
        if response['result'] != summarize(packet):
            raise Blocked('Resultado não corresponde ao contrato do flow experimental.')
        job = uuid.uuid4().hex
        folder = self.root / job
        folder.mkdir()
        # Manifest last: incomplete runs are preserved, never considered committed.
        blobs = {'context.json': raw_json(packet), 'result.json': raw_json(response['result']),
                 'trace.json': raw_json(response['trace'])}
        for name, raw in blobs.items():
            atomic(folder / name, raw)
        atomic(folder / 'manifest.json', {'status': 'LAB_CANDIDATE', 'hashes': {k: digest(v) for k, v in blobs.items()}})
        return job

    def reverse(self, job):
        if not isinstance(job, str) or len(job) != 32 or any(c not in '0123456789abcdef' for c in job):
            raise Blocked('Experiência inválida.')
        folder = self.root / job
        if folder.is_symlink():
            raise Blocked('Experiência redirecionada.')
        try:
            names = {'context.json', 'result.json', 'trace.json'}
            if any((folder / n).is_symlink() for n in names | {'manifest.json'}):
                raise Blocked('Ficheiro redirecionado.')
            manifest = strict_json((folder / 'manifest.json').read_bytes())
            if set(manifest) != {'status', 'hashes'} or manifest['status'] != 'LAB_CANDIDATE' or set(manifest['hashes']) != names:
                raise Blocked('Manifesto experimental inválido.')
            values = {}
            for name in names:
                raw = (folder / name).read_bytes()
                if digest(raw) != manifest['hashes'][name]:
                    raise Blocked('Experiência adulterada.')
                values[name] = strict_json(raw)
            self.revalidate(values['context.json'])
            if values['result.json'] != summarize(values['context.json']):
                raise Blocked('Resultado incoerente.')
            return values
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise Blocked('Não foi possível validar retorno da experiência.') from error

    def uses(self, run_id):
        """Source -> saved lab uses. Conservative: broken experiments stop traversal."""
        self.store.path('runs', run_id)
        uses = []
        for folder in sorted(self.root.iterdir()):
            if folder.is_dir() and len(folder.name) == 32 and all(c in '0123456789abcdef' for c in folder.name):
                packet = self.reverse(folder.name)['context.json']
                if any(source['run_id'] == run_id for source in packet['sources']):
                    uses.append(folder.name)
        return uses
