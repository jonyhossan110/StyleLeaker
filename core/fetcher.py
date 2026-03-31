from __future__ import annotations

import json
import random
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
from requests import Response, Session
from requests.exceptions import RequestException, SSLError, Timeout

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/125.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/125.0.1834.0 Safari/537.36',
]


class Fetcher:
    """HTTP fetcher with session handling, proxies, and retry logic."""

    def __init__(self, logger: Any = None) -> None:
        self.session: Session = requests.Session()
        self.logger = logger

    def _choose_user_agent(self, custom_agent: Optional[str]) -> str:
        if custom_agent:
            return custom_agent
        return random.choice(USER_AGENTS)

    def _build_proxy_dict(self, proxy_url: Optional[str]) -> Optional[Dict[str, str]]:
        if not proxy_url:
            return None
        return {
            'http': proxy_url,
            'https': proxy_url,
        }

    def _parse_cookies(self, cookies: Optional[str]) -> Optional[Dict[str, str]]:
        if not cookies:
            return None
        cookie_dict: Dict[str, str] = {}
        for pair in cookies.split(';'):
            if '=' in pair:
                name, value = pair.split('=', 1)
                cookie_dict[name.strip()] = value.strip()
        return cookie_dict

    def _validate_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme in {'http', 'https'} and parsed.netloc:
            return url
        if not parsed.scheme and parsed.path:
            return f'http://{url}'
        raise ValueError('Invalid URL format')

    def fetch(
        self,
        url: str,
        timeout: int = 10,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
        cookies: Optional[str] = None,
        verify: bool = True,
        user_agent: Optional[str] = None,
    ) -> Optional[Response]:
        """Fetch a URL with timeout, redirect handling, and optional proxy."""
        try:
            validated_url = self._validate_url(url)
        except ValueError as exc:
            if self.logger:
                self.logger.error(f'Invalid URL: {url}')
            return None

        self.session.headers.clear()
        self.session.headers['User-Agent'] = self._choose_user_agent(user_agent)
        self.session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        self.session.headers['Accept-Language'] = 'en-US,en;q=0.9'

        if headers:
            self.session.headers.update(headers)

        # Keep request state isolated per call.
        self.session.cookies.clear()
        self.session.proxies = {}

        cookie_map = self._parse_cookies(cookies)
        if cookie_map:
            self.session.cookies.update(cookie_map)

        proxies = self._build_proxy_dict(proxy)
        if proxies:
            self.session.proxies = proxies

        attempt = 0
        while attempt < 2:
            try:
                response = self.session.get(
                    validated_url,
                    timeout=timeout,
                    allow_redirects=True,
                    verify=verify,
                )
                if response.status_code == 429 and attempt == 0:
                    time.sleep(2)
                    attempt += 1
                    continue
                return response
            except SSLError as exc:
                if self.logger:
                    self.logger.warning(f'SSL error for {url}: {exc}')
                return None
            except Timeout:
                if self.logger:
                    self.logger.error(f'Timeout while fetching {url}')
                return None
            except RequestException as exc:
                if self.logger:
                    self.logger.error(f'Network error fetching {url}: {exc}')
                return None
        return None
