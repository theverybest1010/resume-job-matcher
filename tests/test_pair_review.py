from types import SimpleNamespace as O
from pair_review import build_pair_review

def mention(uri, text, confirmed=True):
    return O(skill=O(uri=uri,preferred_label=uri), matched_text=text,is_confirmed=confirmed)

def test_same_skill_suggestion_requires_review_and_deduplicates():
    r=O(resume_mentions=[mention('security','Computer security',False)],
        job_mentions=[mention('security','Cyber security'),mention('security','Security')])
    rows=build_pair_review(r)
    assert len(rows)==1 and not rows[0]['matched']
    assert len(rows[0]['candidates'])==1
    assert rows[0]['candidates'][0]['resume_text']=='Computer security'

def test_confirmed_overlap_is_automatic():
    rows=build_pair_review(O(resume_mentions=[mention('a','A')],job_mentions=[mention('a','A')]))
    assert rows[0]['matched'] and not rows[0]['candidates']

def test_job_only_suggestion_has_no_invented_resume_evidence():
    rows=build_pair_review(O(resume_mentions=[],job_mentions=[mention('a','A',False)]))
    assert len(rows)==1 and not rows[0]['matched'] and rows[0]['candidates']==[]

def test_related_different_ids_propose_real_evidence_without_awarding_credit():
    class Model:
        def encode(self, texts, **kwargs):
            assert texts==['Cyber security','Computer security']
            return [[1,0],[0.8,0.6]]
    rows=build_pair_review(O(resume_mentions=[mention('computer','Computer security')],
        job_mentions=[mention('cyber','Cyber security')]),Model())
    assert not rows[0]['matched']
    assert rows[0]['candidates'][0]['similarity']==0.8
