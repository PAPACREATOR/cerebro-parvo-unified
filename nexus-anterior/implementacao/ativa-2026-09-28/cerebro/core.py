from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional
import hashlib, json, mimetypes, os, shutil, tempfile, uuid, zipfile

class PolicyUndefined(RuntimeError): pass
class ContractError(RuntimeError): pass
class RecoveryRequired(RuntimeError): pass
class ContentClass(str,Enum): READY="READY"; REVIEW="REVIEW"; FAILED="FAILED"
class CommitState(str,Enum): COMMITTED="COMMITTED"; NOT_COMMITTED="NOT_COMMITTED"; RECOVERY_REQUIRED="RECOVERY_REQUIRED"

@dataclass(frozen=True)
class Policy:
    max_input_bytes:Optional[int]=None; accept_empty:Optional[bool]=None
    adapter_priority:Optional[dict[str,list[str]]]=None; task_timeout_s:Optional[int]=None
    max_result_bytes:Optional[int]=None; ready_rule:Optional[Callable[[dict],ContentClass]]=None
@dataclass(frozen=True)
class ReceivedInput: temp_ref:str; path:Path; filename:str; byte_size:int
@dataclass(frozen=True)
class Operation: operation_id:str; temp_ref:str
@dataclass(frozen=True)
class Attachment: attachment_id:str; operation_id:str; source_path:Path
@dataclass(frozen=True)
class Quarantined: attachment_id:str; path:Path
@dataclass(frozen=True)
class HashResult: attachment_id:str; algorithm:str; digest:str

def new_id(): return str(uuid.uuid4())
def _valid_uuid(value):
    try: uuid.UUID(str(value)); return True
    except (ValueError, TypeError, AttributeError): return False

# IMP-001
def receive_file(path:Path):
    path=Path(path)
    if not path.exists() or not path.is_file(): raise ContractError("RECEIVE_FAILED")
    return ReceivedInput(new_id(),path,path.name,path.stat().st_size)

# IMP-002
def validate_input(x,policy):
    if policy.max_input_bytes is None or policy.accept_empty is None: raise PolicyUndefined("IMP-002 POR DEFINIR")
    if not x.path.exists() or not os.access(x.path,os.R_OK): raise ContractError("InputRejected")
    size=x.path.stat().st_size
    if size!=x.byte_size: raise ContractError("InputRejected: changed")
    if size==0 and not policy.accept_empty: raise ContractError("InputRejected: empty")
    if size>policy.max_input_bytes: raise ContractError("InputRejected: too large")
    return x

# IMP-003/004
def create_operation(x,correlated_operation_id=None):
    if correlated_operation_id is not None and not _valid_uuid(correlated_operation_id): raise ContractError("invalid correlated operation_id")
    return Operation(correlated_operation_id or new_id(),x.temp_ref)
def create_attachment(op,x,correlated_attachment_id=None, correlated_operation_id=None):
    if correlated_attachment_id is not None and not _valid_uuid(correlated_attachment_id): raise ContractError("invalid correlated attachment_id")
    if correlated_attachment_id is not None and correlated_operation_id != op.operation_id:
        raise ContractError("attachment retry lacks proof of same operation")
    return Attachment(correlated_attachment_id or new_id(),op.operation_id,x.path)

# IMP-005
def quarantine(a,directory):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    target=directory/f"{a.attachment_id}.bin"
    if target.exists():
        if not byte_equal(a.source_path,target): raise RecoveryRequired("existing quarantine bytes differ")
        return Quarantined(a.attachment_id,target)
    fd,tmp=tempfile.mkstemp(prefix=a.attachment_id+".",suffix=".partial",dir=directory); os.close(fd); tmp=Path(tmp)
    try:
        shutil.copyfile(a.source_path,tmp)
        if tmp.stat().st_size!=a.source_path.stat().st_size: raise RecoveryRequired("size mismatch")
        os.replace(tmp,target); return Quarantined(a.attachment_id,target)
    except Exception:
        if tmp.exists(): tmp.unlink()
        raise

# IMP-006
def sha256_file(q):
    h=hashlib.sha256()
    with q.path.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""): h.update(chunk)
    return HashResult(q.attachment_id,"sha256",h.hexdigest())

def byte_equal(a,b):
    a,b=Path(a),Path(b)
    if a.stat().st_size!=b.stat().st_size:return False
    with a.open("rb") as fa,b.open("rb") as fb:
        while True:
            x,y=fa.read(1048576),fb.read(1048576)
            if x!=y:return False
            if not x:return True

# IMP-007
def exact_duplicate(q,digest,candidates):
    return [aid for aid,p,d in candidates if d==digest and byte_equal(q.path,p)]

# IMP-008
def detect_format(path):
    path=Path(path); b=path.read_bytes()[:16]
    if b.startswith(b"%PDF-"): return "pdf",{"signature":"%PDF-"}
    if b.startswith(b"\x89PNG\r\n\x1a\n"): return "png",{"signature":"PNG"}
    if b.startswith(b"\xff\xd8\xff"): return "jpeg",{"signature":"JPEG"}
    if b.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as z:
                n=set(z.namelist())
                if "[Content_Types].xml" in n and any(x.startswith("word/") for x in n): return "docx",{"container":"zip"}
                if "mimetype" in n and z.read("mimetype")==b"application/epub+zip": return "epub",{"container":"zip"}
        except Exception:
            return "unknown",{"signature":"PK","container_valid":False}
        return "zip",{"signature":"PK","container_valid":True}
    return "unknown",{"extension_mime":mimetypes.guess_type(str(path))[0]}

# IMP-009/010
def select_adapter(fmt,registry,policy):
    c=registry.get(fmt,[])
    if not c: raise ContractError("no authorized adapter")
    if len(c)==1:return c[0]
    if not policy.adapter_priority or fmt not in policy.adapter_priority: raise PolicyUndefined("IMP-009 POR DEFINIR")
    for x in policy.adapter_priority[fmt]:
        if x in c:return x
    raise ContractError("no prioritized adapter")

def create_task(op,a,adapter,capability,payload,policy):
    if policy.task_timeout_s is None: raise PolicyUndefined("IMP-010 POR DEFINIR")
    return {"task_id":new_id(),"operation_id":op.operation_id,"attachment_id":a.attachment_id,
            "adapter_id":adapter,"capability":capability,"input":payload,"permissions":[],"timeout_s":policy.task_timeout_s}

# IMP-011: Activepieces boundary
def execute_via_activepieces(task,executor): return executor(task)

# IMP-012/013
def receive_untrusted_result(task,result):
    for k in ("task_id","operation_id","attachment_id"):
        if result.get(k)!=task.get(k): raise ContractError("correlation failed: "+k)
    return {"trust":"UNTRUSTED","payload":result}

def validate_envelope(x,policy):
    p=x.get("payload")
    if not isinstance(p,dict): raise ContractError("EnvelopeInvalid")
    if not {"task_id","operation_id","attachment_id","status"}.issubset(p): raise ContractError("EnvelopeInvalid")
    ARCHIVE_REDACTED_04={"authority","canonical","approved","human_approved"}
    if ARCHIVE_REDACTED_04.intersection(p): raise ContractError("EnvelopeInvalid: authority injection")
    if policy.max_result_bytes is None: raise PolicyUndefined("IMP-013 POR DEFINIR")
    if len(json.dumps(p,ensure_ascii=False).encode())>policy.max_result_bytes: raise ContractError("EnvelopeInvalid: too large")
    return p

# IMP-014/015
def validate_content(e):
    r=e.get("result"); failures=[]
    if r is None or (isinstance(r,str) and not r.strip()): failures.append("empty_or_missing_result")
    return {"evidence":{"result_present":r is not None},"warnings":[],"failures":failures}

def classify_content(v,policy):
    if policy.ready_rule is None: raise PolicyUndefined("IMP-015 POR DEFINIR")
    result=policy.ready_rule(v)
    if not isinstance(result,ContentClass): raise ContractError("classifier returned invalid class")
    return result

# IMP-016/017/018
def build_creative_candidate(op,a,content,classification):
    if classification!=ContentClass.READY: raise ContractError("only READY enters Creative")
    if a.operation_id != op.operation_id: raise ContractError("operation/attachment mismatch")
    return {"candidate_id":new_id(),"domain":"CREATIVE","operation_id":op.operation_id,"attachment_id":a.attachment_id,"content":content,"authority":"CANDIDATE"}

def provenance(c,tool,evidence):
    if not isinstance(tool,dict) or not tool.get("id") or not tool.get("version"):
        raise ContractError("provenance requires tool id/version")
    return {"provenance_id":new_id(),"candidate_id":c["candidate_id"],"operation_id":c["operation_id"],
            "attachment_id":c["attachment_id"],"tool":tool,"evidence":evidence}

def prepare_events(c,p):
    return [{"event_id":new_id(),"version":1,"type":"CREATIVE_CANDIDATE_PREPARED","operation_id":c["operation_id"],"payload":{"candidate":c,"provenance":p}}]

# IMP-019: fail closed until G10 is decided
def materialize(events,*a,**kw): raise PolicyUndefined("IMP-019/G10 POR DEFINIR")

# IMP-020/021/022/023
def derivative_status(ok): return "DERIVATIVES_UPDATED" if ok else "DERIVATIVES_DIRTY"
def present(status,label):
    return {"COMMITTED":f"{label} — Importado","REVIEW":f"{label} — Precisa de verificação","FAILED":f"{label} — Falhou"}.get(status,f"{label} — {status}")
def failure(step,reason,uncertain_commit=False,retry_safe=False):
    return {"step":step,"reason":reason,"state":"RECOVERY_REQUIRED" if uncertain_commit else ("RETRYABLE" if retry_safe else "FAILED")}
def reconcile(e):
    committed=bool(e.get("commit_receipt") and e.get("state_hash_verified"))
    not_committed=bool(e.get("proved_no_commit"))
    if committed and not_committed: return CommitState.RECOVERY_REQUIRED
    if committed: return CommitState.COMMITTED
    if not_committed: return CommitState.NOT_COMMITTED
    return CommitState.RECOVERY_REQUIRED

# IMP-024/025/026
def deletion_proposal(attachment_id,exists,refs):
    return {"proposal_id":new_id(),"attachment_id":attachment_id,"exists":exists,"references":list(refs),"effect":"DELETE_ORIGINAL_ONLY"}
def authorize_deletion(proposal,human_decision,target_attachment_id):
    if proposal["attachment_id"]!=target_attachment_id: raise ContractError("authorization target mismatch")
    if not proposal.get("exists"): raise ContractError("cannot approve deletion of unresolved/nonexistent target")
    return {"authorization_id":new_id(),"proposal_id":proposal["proposal_id"],"attachment_id":target_attachment_id,"approved":bool(human_decision),"actor":"HUMAN"}
def delete_authorized_original(authorization,original):
    if not authorization.get("approved"): raise ContractError("deletion not approved")
    raise PolicyUndefined("IMP-026 original/backup semantics POR DEFINIR")
