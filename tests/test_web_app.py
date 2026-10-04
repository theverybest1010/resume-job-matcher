import io
from pathlib import Path
from types import SimpleNamespace as Obj

import pytest

from web_app import create_app


def pdf_bytes():
    # Small real PDF fixture; no NLP/model downloads are needed by web tests.
    stream = b'BT /F1 12 Tf 72 720 Td (Python developer with Java experience.) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream']
    result = bytearray(b'%PDF-1.4\n'); offsets = [0]
    for i, body in enumerate(objects, 1):
        offsets.append(len(result)); result.extend(f'{i} 0 obj\n'.encode() + body + b'\nendobj\n')
    start = len(result)
    result.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:
        result.extend(f'{offset:010d} 00000 n \n'.encode())
    result.extend(f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode())
    return bytes(result)


def report():
    skill = Obj(uri='test:python', preferred_label='Python')
    mention = Obj(skill=skill, matched_text='Python', source='exact', is_confirmed=True)
    return Obj(skill_gap=Obj(matched_skills=[skill], missing_skills=[], additional_skills=[], match_percentage=100),
               tfidf_similarity=.4, resume_mentions=[mention], job_mentions=[mention],
               resume_suggestions=[], job_suggestions=[])


@pytest.fixture
def service():
    calls = []
    def analyze(resume, job):
        calls.append((resume, job)); return report()
    builds = []
    def factory():
        builds.append(True); return Obj(analyze=analyze)
    app = create_app(factory)
    app.config['TESTING'] = True
    return app.test_client(), calls, builds


def upload(**extra):
    return {'resume': (io.BytesIO(pdf_bytes()), 'resume.pdf'), **extra}


def test_pdf_and_pasted_job_reuse_pipeline(service):
    client, calls, builds = service
    for _ in range(2):
        response = client.post('/api/compare', data=upload(job_text='Python engineer'))
        assert response.status_code == 200
        assert response.json['coverage'] == 100
        assert response.json['required_count'] == 1
        assert response.headers['Cache-Control'] == 'no-store'
    assert len(builds) == 1
    assert 'Python developer' in calls[0][0]
    assert calls[0][1] == 'Python engineer'


def test_link_input(service, monkeypatch):
    import job_links
    monkeypatch.setattr(job_links, 'fetch_job_text', lambda url: 'Python job from a public posting')
    client, calls, _ = service
    assert client.post('/api/compare', data=upload(job_url='https://jobs.example/role')).status_code == 200
    assert calls[0][1] == 'Python job from a public posting'


def test_link_error_offers_paste_fallback(service, monkeypatch):
    import job_links
    def blocked(url):
        raise ValueError('The job site did not allow access. Paste its job description instead.')
    monkeypatch.setattr(job_links, 'fetch_job_text', blocked)
    response = service[0].post('/api/compare', data=upload(job_url='https://jobs.example/role'))
    assert response.status_code == 400
    assert 'Paste' in response.json['error']
    assert not service[2]


@pytest.mark.parametrize('data', [
    {'job_text': 'Python'},
    {'resume': (io.BytesIO(b'hello'), 'resume.txt'), 'job_text': 'Python'},
    {'resume': (io.BytesIO(b'bad pdf'), 'resume.pdf'), 'job_text': 'Python'},
])
def test_invalid_uploads_rejected_before_model(service, data):
    response = service[0].post('/api/compare', data=data)
    assert response.status_code == 400
    assert response.is_json
    assert not service[2]


@pytest.mark.parametrize('extra', [{}, {'job_text': 'Python', 'job_url': 'https://example.com'}, {'job_text': 'x' * 50001}])
def test_job_validation(service, extra):
    assert service[0].post('/api/compare', data=upload(**extra)).status_code == 400
    assert not service[2]


def test_large_upload(service):
    response = service[0].post('/api/compare', data={
        'resume': (io.BytesIO(b'x' * (5 * 1024 * 1024 + 1)), 'resume.pdf'), 'job_text': 'Python',
    })
    assert response.status_code == 400
    assert '5 MB' in response.json['error']


def test_temporary_files_removed(service, monkeypatch):
    from resume_matcher import document_loader
    original = document_loader.extract_document_text
    seen = []
    def record(path):
        seen.append(Path(path)); return original(path)
    monkeypatch.setattr(document_loader, 'extract_document_text', record)
    assert service[0].post('/api/compare', data=upload(job_text='Python')).status_code == 200
    assert seen and all(not p.exists() and not p.parent.exists() for p in seen)


def test_no_confirmed_job_skills_and_startup_failure():
    r = report(); r.skill_gap.matched_skills = []; r.skill_gap.match_percentage = 0
    client = create_app(lambda: Obj(analyze=lambda *args: r)).test_client()
    assert client.post('/api/compare', data=upload(job_text='Python')).json['coverage'] is None
    def broken():
        raise FileNotFoundError('/private/path')
    response = create_app(broken).test_client().post('/api/compare', data=upload(job_text='Python'))
    assert response.status_code == 503
    assert '/private/path' not in response.get_data(as_text=True)


def test_home_has_pdf_and_two_job_modes(service):
    page = service[0].get('/').get_data(as_text=True)
    assert 'application/pdf' in page and 'Use a link' in page and 'Paste text' in page
