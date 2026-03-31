from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from requests import Response

from .fetcher import Fetcher
from utils.logger import Logger

HEADERS_TO_CHECK = [
    'X-Powered-By',
    'Server',
    'X-Generator',
    'Strict-Transport-Security',
    'Content-Security-Policy',
    'X-Frame-Options',
    'X-XSS-Protection',
]


class Recon:
    """Reconnaissance module for HTTP headers, robots.txt, and sitemap.xml."""

    def __init__(self, fetcher: Fetcher, logger: Logger) -> None:
        self.fetcher = fetcher
        self.logger = logger

    def run(self, base_url: str, response: Response) -> Dict[str, Any]:
        """Execute reconnaissance and return findings."""
        findings: Dict[str, Any] = {
            'headers': self._analyze_security_headers(response.headers),
            'robots': self._fetch_robots_txt(base_url),
            'sitemap': self._fetch_sitemap_xml(base_url),
        }
        return findings

    def _analyze_security_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        report: Dict[str, Dict[str, str]] = {}
        for header in HEADERS_TO_CHECK:
            value = headers.get(header, '').strip()
            status = self._header_status(header, value)
            report[header] = {
                'value': value or 'MISSING',
                'status': status,
            }
        return {
            'findings': report,
            'raw_headers': {k: v for k, v in headers.items()},
        }

    def _header_status(self, header: str, value: str) -> str:
        if not value:
            return 'MISSING'
        if header in {'X-Powered-By', 'Server', 'X-Generator'}:
            return 'FAIL'
        if header == 'Strict-Transport-Security':
            return 'PASS'
        if header == 'Content-Security-Policy':
            return 'PASS' if 'default-src' in value.lower() or 'script-src' in value.lower() else 'WARN'
        if header == 'X-Frame-Options':
            return 'PASS'
        if header == 'X-XSS-Protection':
            return 'PASS' if value.lower() not in {'0', 'disabled'} else 'FAIL'
        return 'PASS'

    def _fetch_robots_txt(self, base_url: str) -> Dict[str, Any]:
        robots_url = urljoin(base_url, '/robots.txt')
        response = self.fetcher.fetch(robots_url)
        if not response or response.status_code >= 400:
            self.logger.warning(f'Unable to fetch robots.txt from {robots_url}')
            return {'disallowed_paths': [], 'source': robots_url}

        paths = self._parse_robots_txt(response.text)
        return {
            'disallowed_paths': paths,
            'source': robots_url,
        }

    def _parse_robots_txt(self, content: str) -> List[str]:
        disallowed: List[str] = []
        for line in content.splitlines():
            normalized = line.strip()
            if not normalized or normalized.startswith('#'):
                continue
            if normalized.lower().startswith('disallow:'):
                _, path = normalized.split(':', 1)
                path = path.strip()
                if path:
                    disallowed.append(path)
        return sorted(set(disallowed))

    def _fetch_sitemap_xml(self, base_url: str) -> Dict[str, Any]:
        sitemap_url = urljoin(base_url, '/sitemap.xml')
        response = self.fetcher.fetch(sitemap_url)
        if not response or response.status_code >= 400:
            self.logger.warning(f'Unable to fetch sitemap.xml from {sitemap_url}')
            return {'urls': [], 'source': sitemap_url}

        urls = self._parse_sitemap_xml(response.text)
        return {
            'urls': urls,
            'source': sitemap_url,
        }

    def _parse_sitemap_xml(self, content: str) -> List[str]:
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return []

        urls: List[str] = []
        for loc in root.findall('.//{*}loc'):
            if loc.text:
                urls.append(loc.text.strip())
        if not urls:
            for loc in root.findall('.//loc'):
                if loc.text:
                    urls.append(loc.text.strip())
        return sorted(set(urls))
