import hashlib, pytest
from pathlib import Path
from cerebro.core import *
def pol(): return Policy(max_input_bytes=10000,accept_empty=False,task_timeout_s=30,max_result_bytes=10000,ready_rule=lambda v: ContentClass.FAILED if v["failures"] else ContentClass.READY)
def test_imp001_007(tmp_path):
 p=tmp_path/"orig"; p.write_bytes(b"abc"); r=receive_file(p); validate_input(r,pol()); o=create_operation(r); a=create_attachment(o,r); q=quarantine(a,tmp_path/"q"); h=sha256_file(q)
 assert p.read_bytes()==b"abc"; assert h.digest==hashlib.sha256(b"abc").hexdigest()
 c=tmp_path/"copy"; c.write_bytes(b"abc"); assert exact_duplicate(q,h.digest,[("x",c,h.digest)])==["x"]
def test_distinct_receptions_distinct_operations(tmp_path):
 p=tmp_path/"a";p.write_bytes(b"x"); assert create_operation(receive_file(p)).operation_id!=create_operation(receive_file(p)).operation_id
def test_quarantine_retry(tmp_path):
 p=tmp_path/"a";p.write_bytes(b"x");r=receive_file(p);a=create_attachment(create_operation(r),r); assert quarantine(a,tmp_path/"q").path==quarantine(a,tmp_path/"q").path
def test_format_content_beats_extension(tmp_path):
 p=tmp_path/"x.txt";p.write_bytes(b"%PDF-1.7\n");assert detect_format(p)[0]=="pdf"
def test_wrong_correlation_rejected():
 t={"task_id":"t","operation_id":"o","attachment_id":"a"}
 with pytest.raises(ContractError):receive_untrusted_result(t,{"task_id":"t","operation_id":"BAD","attachment_id":"a"})
def test_review_cannot_enter_creative():
 with pytest.raises(ContractError):build_creative_candidate(Operation("o","t"),Attachment("a","o",Path("x")),"x",ContentClass.REVIEW)
def test_reconcile_closed():
 assert reconcile({})==CommitState.RECOVERY_REQUIRED;assert reconcile({"proved_no_commit":True})==CommitState.NOT_COMMITTED;assert reconcile({"commit_receipt":True,"state_hash_verified":True})==CommitState.COMMITTED
def test_undefined_policy_blocks(tmp_path):
 p=tmp_path/"a";p.write_bytes(b"x")
 with pytest.raises(PolicyUndefined):validate_input(receive_file(p),Policy())
 with pytest.raises(PolicyUndefined):materialize([])
def test_deletion_requires_human_contract():
 p=deletion_proposal("a",True,[]);a=authorize_deletion(p,True,"a");assert a["actor"]=="HUMAN"
