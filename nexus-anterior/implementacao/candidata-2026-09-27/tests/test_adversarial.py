import pytest
from pathlib import Path
from cerebro.core import *

def P(): return Policy(max_input_bytes=100, accept_empty=False, task_timeout_s=10, max_result_bytes=500, ready_rule=lambda v: ContentClass.READY if not v['failures'] else ContentClass.FAILED)

def test_existing_quarantine_with_wrong_bytes_must_not_succeed(tmp_path):
    src=tmp_path/'src'; src.write_bytes(b'GOOD')
    r=receive_file(src); o=create_operation(r); a=create_attachment(o,r)
    qdir=tmp_path/'q'; qdir.mkdir(); (qdir/f'{a.attachment_id}.bin').write_bytes(b'EVIL')
    with pytest.raises(RecoveryRequired): quarantine(a,qdir)

def test_correlated_ids_must_be_valid_uuid(tmp_path):
    p=tmp_path/'x'; p.write_bytes(b'x'); r=receive_file(p)
    with pytest.raises(ContractError): create_operation(r,'not-a-uuid')

def test_attachment_retry_requires_same_operation(tmp_path):
    p=tmp_path/'x';p.write_bytes(b'x');r=receive_file(p)
    o1=create_operation(r); o2=create_operation(r)
    a=create_attachment(o1,r)
    with pytest.raises(ContractError): create_attachment(o2,r,a.attachment_id)

def test_duplicate_digest_collision_not_enough(tmp_path):
    a=tmp_path/'a'; b=tmp_path/'b'; a.write_bytes(b'abc'); b.write_bytes(b'abd')
    q=Quarantined('new',a)
    assert exact_duplicate(q,'forced',[('old',b,'forced')])==[]

def test_invalid_zip_is_not_claimed_as_zip(tmp_path):
    p=tmp_path/'bad.zip'; p.write_bytes(b'PK\x03\x04garbage')
    fmt,_=detect_format(p)
    assert fmt=='unknown'

def test_activepieces_exception_never_becomes_success():
    def boom(task): raise TimeoutError('timeout')
    with pytest.raises(TimeoutError): execute_via_activepieces({'task_id':'t'},boom)

def test_envelope_extra_authority_field_rejected():
    task={'task_id':'t','operation_id':'o','attachment_id':'a'}
    result={**task,'status':'OK','authority':'CANONICAL','result':'x'}
    u=receive_untrusted_result(task,result)
    with pytest.raises(ContractError): validate_envelope(u,P())

def test_classifier_cannot_return_arbitrary_value():
    p=P(); p=Policy(**{**p.__dict__,'ready_rule':lambda v:'READY'})
    with pytest.raises(ContractError): classify_content({'failures':[]},p)

def test_creative_requires_matching_operation_attachment():
    o=Operation(new_id(),'t'); a=Attachment(new_id(),new_id(),Path('x'))
    with pytest.raises(ContractError): build_creative_candidate(o,a,'x',ContentClass.READY)

def test_provenance_requires_tool_identity():
    c={'candidate_id':new_id(),'operation_id':new_id(),'attachment_id':new_id()}
    with pytest.raises(ContractError): provenance(c,{}, {})

def test_reconcile_conflicting_evidence_fails_closed():
    assert reconcile({'commit_receipt':True,'state_hash_verified':True,'proved_no_commit':True})==CommitState.RECOVERY_REQUIRED

def test_deletion_nonexistent_target_not_approvable():
    p=deletion_proposal(new_id(),False,[])
    with pytest.raises(ContractError): authorize_deletion(p,True,p['attachment_id'])

def test_source_change_after_receive_rejected(tmp_path):
    p=tmp_path/'x'; p.write_bytes(b'a'); r=receive_file(p); p.write_bytes(b'bb')
    with pytest.raises(ContractError): validate_input(r,P())

def test_size_boundary_exactly_max_allowed(tmp_path):
    p=tmp_path/'x'; p.write_bytes(b'x'*100); r=receive_file(p); assert validate_input(r,P())==r

def test_size_boundary_over_max_rejected(tmp_path):
    p=tmp_path/'x'; p.write_bytes(b'x'*101); r=receive_file(p)
    with pytest.raises(ContractError): validate_input(r,P())

def test_empty_rejected_by_policy(tmp_path):
    p=tmp_path/'x'; p.write_bytes(b''); r=receive_file(p)
    with pytest.raises(ContractError): validate_input(r,P())

def test_exact_duplicate_does_not_delete_anything(tmp_path):
    a=tmp_path/'a';b=tmp_path/'b';a.write_bytes(b'x');b.write_bytes(b'x');q=Quarantined(new_id(),a)
    exact_duplicate(q,'h',[('old',b,'h')]); assert a.exists() and b.exists()

def test_unknown_extension_does_not_define_format(tmp_path):
    p=tmp_path/'thing.pdf'; p.write_bytes(b'not a pdf'); assert detect_format(p)[0]=='unknown'

def test_adapter_ambiguity_fails_closed():
    with pytest.raises(PolicyUndefined): select_adapter('pdf',{'pdf':['a','b']},P())

def test_result_missing_ids_rejected():
    t={'task_id':'t','operation_id':'o','attachment_id':'a'}
    with pytest.raises(ContractError): receive_untrusted_result(t,{'task_id':'t'})

def test_materialize_still_blocked():
    with pytest.raises(PolicyUndefined): materialize([{'event_id':new_id()}])

def test_present_review_never_says_imported():
    assert 'Importado' not in present('REVIEW','x')

def test_retryable_not_given_when_commit_uncertain():
    x=failure('x','y',uncertain_commit=True,retry_safe=True); assert x['state']=='RECOVERY_REQUIRED'

def test_authorization_target_cannot_expand():
    p=deletion_proposal(new_id(),True,[])
    with pytest.raises(ContractError): authorize_deletion(p,True,new_id())

def test_delete_stays_blocked_even_when_approved():
    p=deletion_proposal(new_id(),True,[]); a=authorize_deletion(p,True,p['attachment_id'])
    with pytest.raises(PolicyUndefined): delete_authorized_original(a,Path('x'))
