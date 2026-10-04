import socket

import pytest
import job_links


@pytest.mark.parametrize('ip', ['127.0.0.1', '10.0.0.1', '169.254.169.254', '::1', '192.168.1.2'])
def test_private_dns_is_rejected(monkeypatch, ip):
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [(2, 1, 6, '', (ip, 443))])
    with pytest.raises(ValueError, match='public'):
        job_links.public_target('https://example.com/job')


@pytest.mark.parametrize('url', ['file:///etc/passwd', 'https://user:secret@example.com/', 'https://example.com:444/'])
def test_disallowed_url_forms(url):
    with pytest.raises(ValueError):
        job_links.public_target(url)


def test_public_ip_is_pinned_and_html_extracted(monkeypatch):
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [(2, 1, 6, '', ('93.184.216.34', 443))])
    made = []
    class Response:
        status = 200
        headers = {'Content-Type': 'text/html'}
        def read(self, *a, **k):
            return b'<h1>Python Engineer</h1><script>secret script</script><p>Build software.</p>'
        def close(self): pass
    class Pool:
        def __init__(self, host, port, **kwargs): made.append((host, kwargs))
        def urlopen(self, *a, **k): return Response()
        def close(self): pass
    monkeypatch.setattr(job_links.urllib3, 'HTTPSConnectionPool', Pool)
    assert job_links.fetch_job_text('https://example.com/job') == 'Python Engineer\nBuild software.'
    assert made[0][0] == '93.184.216.34'
    assert made[0][1]['server_hostname'] == 'example.com'
    assert made[0][1]['assert_hostname'] == 'example.com'


def test_redirect_to_private_address_is_blocked(monkeypatch):
    def resolve(host, *a, **k):
        ip = '93.184.216.34' if host == 'example.com' else '127.0.0.1'
        return [(2, 1, 6, '', (ip, 443))]
    monkeypatch.setattr(socket, 'getaddrinfo', resolve)
    class Response:
        status = 302
        headers = {'Location': 'https://internal.example/'}
        def close(self): pass
    class Pool:
        def __init__(self, *a, **k): pass
        def urlopen(self, *a, **k): return Response()
        def close(self): pass
    monkeypatch.setattr(job_links.urllib3, 'HTTPSConnectionPool', Pool)
    with pytest.raises(ValueError, match='public'):
        job_links.fetch_job_text('https://example.com/job')
