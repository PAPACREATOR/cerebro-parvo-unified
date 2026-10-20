import pytest
from cerebro.persistence import RecoverableMarkdownWriter, PersistenceError, RecoveryRequired

def W(tmp_path): return RecoverableMarkdownWriter(tmp_path/"state"/"cerebro.sqlite3",tmp_path/"vault")

def test_write_creative(tmp_path):
    w=W(tmp_path); r=w.write("op1","CREATIVE","project/a.md","# A\n")
    assert r.state=="COMMITTED"
    assert (tmp_path/"vault"/"creative"/"project"/"a.md").read_text()=="# A\n"
    assert w.reconcile("op1")=="COMMITTED"

def test_idempotent(tmp_path):
    w=W(tmp_path); a=w.write("op1","CREATIVE","a.md","same"); b=w.write("op1","CREATIVE","a.md","same")
    assert a.expected_hash==b.expected_hash and b.state=="COMMITTED"

def test_operation_reuse_diff_payload_rejected(tmp_path):
    w=W(tmp_path); w.write("op1","CREATIVE","a.md","one")
    with pytest.raises(RecoveryRequired): w.write("op1","CREATIVE","a.md","two")

def test_existing_different_target_rejected(tmp_path):
    w=W(tmp_path); p=tmp_path/"vault"/"creative"/"a.md"; p.parent.mkdir(parents=True); p.write_text("old")
    with pytest.raises(RecoveryRequired): w.write("op1","CREATIVE","a.md","new")

def test_crash_after_prepared_resume(tmp_path):
    w=W(tmp_path)
    with pytest.raises(RuntimeError): w.write("op1","CREATIVE","a.md","payload",failpoint="after_prepared")
    assert w.reconcile("op1")=="NOT_COMMITTED"
    assert w.resume("op1").state=="COMMITTED"
    assert (tmp_path/"vault"/"creative"/"a.md").read_text()=="payload"

def test_crash_after_replace_reconcile(tmp_path):
    w=W(tmp_path)
    with pytest.raises(RuntimeError): w.write("op1","CREATIVE","a.md","payload",failpoint="after_replace")
    assert w.reconcile("op1")=="COMMITTED"

def test_committed_missing_requires_recovery(tmp_path):
    w=W(tmp_path); w.write("op1","CREATIVE","a.md","payload"); (tmp_path/"vault"/"creative"/"a.md").unlink()
    assert w.reconcile("op1")=="RECOVERY_REQUIRED"
    with pytest.raises(RecoveryRequired): w.resume("op1")

def test_prepared_divergent_requires_recovery(tmp_path):
    w=W(tmp_path)
    with pytest.raises(RuntimeError): w.write("op1","CREATIVE","a.md","payload",failpoint="after_prepared")
    p=tmp_path/"vault"/"creative"/"a.md"; p.parent.mkdir(parents=True); p.write_text("evil")
    assert w.reconcile("op1")=="RECOVERY_REQUIRED"

def test_canonical_same_writer_separate_domain(tmp_path):
    w=W(tmp_path); w.write("op-c","CANONICAL","x.md","approved")
    assert (tmp_path/"vault"/"canonical"/"x.md").read_text()=="approved"
    assert not (tmp_path/"vault"/"creative"/"x.md").exists()

@pytest.mark.parametrize("path",["../escape.md","x/../../escape.md"])
def test_escape_rejected(tmp_path,path):
    w=W(tmp_path)
    with pytest.raises(PersistenceError): w.write("op","CREATIVE",path,"x")
