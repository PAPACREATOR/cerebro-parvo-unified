from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import hashlib, os, sqlite3, tempfile, time

class PersistenceError(RuntimeError): pass
class RecoveryRequired(PersistenceError): pass

@dataclass(frozen=True)
class MaterializationReceipt:
    operation_id: str
    domain: str
    relative_path: str
    expected_hash: str
    state: str

class RecoverableMarkdownWriter:
    DOMAINS={"CREATIVE","CANONICAL"}

    def __init__(self, db_path:Path, vault_root:Path):
        self.db_path=Path(db_path); self.vault_root=Path(vault_root)
        self.db_path.parent.mkdir(parents=True,exist_ok=True); self.vault_root.mkdir(parents=True,exist_ok=True)
        self._init_db()

    def _connect(self):
        con=sqlite3.connect(self.db_path)
        con.row_factory=sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        return con

    def _init_db(self):
        with self._connect() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS materializations(
            operation_id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            content TEXT NOT NULL,
            expected_hash TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('PREPARED','COMMITTED')),
            prepared_at REAL NOT NULL,
            committed_at REAL)""")

    @staticmethod
    def _hash_bytes(data:bytes)->str: return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _hash_file(path:Path)->str:
        h=hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
        return h.hexdigest()

    def _resolve_target(self,domain,relative_path):
        if domain not in self.DOMAINS: raise PersistenceError("invalid domain")
        rel=Path(relative_path)
        if rel.is_absolute() or ".." in rel.parts or not rel.parts: raise PersistenceError("invalid relative path")
        root=(self.vault_root/domain.lower()).resolve()
        target=(root/rel).resolve()
        try: target.relative_to(root)
        except ValueError as e: raise PersistenceError("path escapes domain root") from e
        return target

    def _row(self,operation_id):
        with self._connect() as con:
            return con.execute("SELECT * FROM materializations WHERE operation_id=?",(operation_id,)).fetchone()

    @staticmethod
    def _receipt(row):
        return MaterializationReceipt(row["operation_id"],row["domain"],row["relative_path"],row["expected_hash"],row["state"])

    def prepare(self,operation_id,domain,relative_path,content):
        if not operation_id or not isinstance(content,str): raise PersistenceError("invalid operation/content")
        target=self._resolve_target(domain,relative_path)
        expected=self._hash_bytes(content.encode("utf-8"))
        existing=self._row(operation_id)
        if existing:
            if (existing["domain"],existing["relative_path"],existing["expected_hash"],existing["content"]) != (domain,relative_path,expected,content):
                raise RecoveryRequired("operation_id reused with different materialization")
            return self._receipt(existing)
        if target.exists() and self._hash_file(target)!=expected:
            raise RecoveryRequired("target already exists with different bytes")
        with self._connect() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute("""INSERT INTO materializations
            (operation_id,domain,relative_path,content,expected_hash,state,prepared_at,committed_at)
            VALUES (?,?,?,?,?,'PREPARED',?,NULL)""",(operation_id,domain,relative_path,content,expected,time.time()))
        return MaterializationReceipt(operation_id,domain,relative_path,expected,"PREPARED")

    def write(self,operation_id,domain,relative_path,content,failpoint:Optional[str]=None):
        receipt=self.prepare(operation_id,domain,relative_path,content)
        if failpoint=="after_prepared": raise RuntimeError("SIMULATED_CRASH_AFTER_PREPARED")
        row=self._row(operation_id)
        if row["state"]=="COMMITTED":
            return self._verify_committed(row)
        target=self._resolve_target(domain,relative_path)
        target.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp_name=tempfile.mkstemp(prefix=f".{operation_id}.",suffix=".partial",dir=target.parent)
        tmp=Path(tmp_name)
        try:
            with os.fdopen(fd,"wb") as f:
                f.write(content.encode("utf-8")); f.flush(); os.fsync(f.fileno())
            if self._hash_file(tmp)!=receipt.expected_hash: raise RecoveryRequired("temporary file hash mismatch")
            os.replace(tmp,target); self._fsync_dir(target.parent)
            if failpoint=="after_replace": raise RuntimeError("SIMULATED_CRASH_AFTER_REPLACE")
            return self._mark_committed(operation_id,target,receipt.expected_hash)
        finally:
            if tmp.exists(): tmp.unlink()

    def reconcile(self,operation_id):
        row=self._row(operation_id)
        if row is None: return "NOT_COMMITTED"
        target=self._resolve_target(row["domain"],row["relative_path"])
        if row["state"]=="COMMITTED":
            return "COMMITTED" if target.exists() and self._hash_file(target)==row["expected_hash"] else "RECOVERY_REQUIRED"
        if not target.exists(): return "NOT_COMMITTED"
        if self._hash_file(target)==row["expected_hash"]:
            self._mark_committed(operation_id,target,row["expected_hash"]); return "COMMITTED"
        return "RECOVERY_REQUIRED"

    def resume(self,operation_id):
        state=self.reconcile(operation_id)
        if state=="COMMITTED": return self._receipt(self._row(operation_id))
        if state=="RECOVERY_REQUIRED": raise RecoveryRequired("cannot automatically resume divergent state")
        row=self._row(operation_id)
        if row is None: raise PersistenceError("unknown operation")
        return self.write(operation_id,row["domain"],row["relative_path"],row["content"])

    def _verify_committed(self,row):
        target=self._resolve_target(row["domain"],row["relative_path"])
        if not target.exists() or self._hash_file(target)!=row["expected_hash"]:
            raise RecoveryRequired("committed receipt disagrees with filesystem")
        return self._receipt(row)

    def _mark_committed(self,operation_id,target,expected_hash):
        if not target.exists() or self._hash_file(target)!=expected_hash:
            raise RecoveryRequired("cannot commit without verified bytes")
        with self._connect() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute("UPDATE materializations SET state='COMMITTED', committed_at=? WHERE operation_id=?",(time.time(),operation_id))
        return self._receipt(self._row(operation_id))

    @staticmethod
    def _fsync_dir(path):
        if os.name=="nt": return
        fd=os.open(path,os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
