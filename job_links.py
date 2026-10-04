"""Read public job pages with bounded downloads and public-address checks."""
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
import urllib3


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'noscript', 'svg'}:
            self.hidden += 1
        if not self.hidden and tag in {'p', 'div', 'li', 'br', 'h1', 'h2', 'h3', 'section'}:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in {'script', 'style', 'noscript', 'svg'} and self.hidden:
            self.hidden -= 1
        if not self.hidden and tag in {'p', 'div', 'li', 'section'}:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def public_target(url):
    parts = urlsplit(url)
    if parts.scheme not in {'https', 'http'} or not parts.hostname or parts.username or parts.password:
        raise ValueError('Use a public http:// or https:// job link.')
    port = parts.port or (443 if parts.scheme == 'https' else 80)
    if port != (443 if parts.scheme == 'https' else 80):
        raise ValueError('This link uses an unsupported port. Paste the job text instead.')
    host = parts.hostname.encode('idna').decode('ascii')
    addresses = {entry[4][0] for entry in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError('Use a public job page, or paste the job description.')
    # Connect to the validated IP, not a second DNS lookup (prevents rebinding).
    return parts, host, port, sorted(addresses)[0]


def fetch_job_text(url):
    if len(url) > 2048:
        raise ValueError('That link is too long. Paste the job description instead.')
    try:
        for _ in range(4):
            parts, host, port, ip = public_target(url)
            kwargs = {'timeout': urllib3.Timeout(connect=5, read=10), 'retries': False}
            if parts.scheme == 'https':
                pool = urllib3.HTTPSConnectionPool(ip, port, server_hostname=host,
                                                  assert_hostname=host, **kwargs)
            else:
                pool = urllib3.HTTPConnectionPool(ip, port, **kwargs)
            response = None
            try:
                path = parts.path or '/'
                if parts.query:
                    path += '?' + parts.query
                response = pool.urlopen('GET', path, headers={
                    'Host': host, 'User-Agent': 'ResumeMatch/0.1', 'Accept-Encoding': 'identity',
                }, redirect=False, preload_content=False)
                if response.status in {301, 302, 303, 307, 308}:
                    target = response.headers.get('Location')
                    if not target:
                        raise ValueError('The job page redirected without a destination.')
                    url = urljoin(url, target)
                    continue
                if response.status != 200:
                    raise ValueError('The job site did not allow access. Paste its job description instead.')
                if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
                    raise ValueError('This page could not be imported. Paste the job description instead.')
                content_type = response.headers.get('Content-Type', '').lower()
                if not any(t in content_type for t in ('text/html', 'text/plain')):
                    raise ValueError('Use a job webpage link, or paste its text.')
                body = response.read(2 * 1024 * 1024 + 1, decode_content=False)
                if len(body) > 2 * 1024 * 1024:
                    raise ValueError('This page is too large to import. Paste the job description instead.')
                text = body.decode('utf-8', errors='replace')
                if 'text/html' in content_type:
                    parser = PageText()
                    parser.feed(text)
                    text = ''.join(parser.parts)
                text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
                if not text or len(text) > 50000:
                    raise ValueError('Could not extract a usable job description. Paste its text instead.')
                return text
            finally:
                if response is not None:
                    response.close()
                pool.close()
        raise ValueError('Too many redirects. Paste the job description instead.')
    except ValueError:
        raise
    except Exception:
        raise ValueError('Could not access that page. It may require sign-in or block imports. Paste the job description instead.') from None
