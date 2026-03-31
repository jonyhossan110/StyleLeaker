from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from .fetcher import Fetcher
from utils.file_handler import normalize_filename, save_text_file

IMPORT_PATTERN = re.compile(r'@import\s+(?:url\()?\s*["\']?(.*?)["\']?\s*\)?\s*;', re.IGNORECASE)
COMMENT_PATTERN = re.compile(r'/\*.*?\*/', re.DOTALL)
VARIABLE_PATTERN = re.compile(r'(--[\w-]+)\s*:\s*([^;]+);')
MEDIA_PATTERN = re.compile(r'@media\s+([^{]+)\{', re.IGNORECASE)
SELECTOR_PATTERN = re.compile(r'([^{]+)\{')


class CSSExtractor:
    """CSS extraction engine for downloading and analyzing CSS assets."""

    def __init__(
        self,
        fetcher: Fetcher,
        logger: Any,
        no_download: bool = False,
        max_depth: int = 2,
    ) -> None:
        self.fetcher = fetcher
        self.logger = logger
        self.no_download = no_download
        self.max_depth = max_depth
        self.visited_urls: set[str] = set()

    def _resolve_url(self, asset_url: str, base_url: str) -> str:
        return urljoin(base_url, asset_url.strip())

    def _extract_filename(self, url: str) -> str:
        parsed = urlparse(url)
        name = Path(parsed.path).name
        if not name or '.' not in name:
            name = f'{parsed.netloc.replace(".", "_")}.css'
        return normalize_filename(name, default='style.css')

    def _extract_comments(self, content: str) -> List[str]:
        return [comment.strip() for comment in COMMENT_PATTERN.findall(content)]

    def _extract_variables(self, content: str) -> List[str]:
        return [f'{name}: {value.strip()}' for name, value in VARIABLE_PATTERN.findall(content)]

    def _extract_media_queries(self, content: str) -> List[str]:
        return [media.strip() for media in MEDIA_PATTERN.findall(content)]

    def _extract_selectors(self, content: str) -> List[str]:
        selectors: set[str] = set()
        for match in SELECTOR_PATTERN.findall(content):
            raw = match.strip()
            raw = raw.replace('\n', ' ').strip()
            if raw and not raw.startswith('@'):
                for part in raw.split(','):
                    selector = part.strip()
                    if selector:
                        selectors.add(selector)
        return sorted(selectors)

    def _parse_imports(self, content: str) -> List[str]:
        return [match for match in IMPORT_PATTERN.findall(content) if match.strip()]

    def _save_css(self, css_url: str, content: str, output_dir: Path) -> Path:
        filename = self._extract_filename(css_url)
        target_path = output_dir / filename
        return save_text_file(target_path, content)

    def _download_css_recursive(
        self,
        css_url: str,
        base_url: str,
        output_dir: Path,
        depth: int,
    ) -> List[Dict[str, Any]]:
        if depth < 0:
            return []
        resolved_url = self._resolve_url(css_url, base_url)
        if resolved_url in self.visited_urls:
            return []
        self.visited_urls.add(resolved_url)

        response = self.fetcher.fetch(resolved_url)
        if not response:
            self.logger.warning(f'Skipping CSS asset due to fetch failure: {resolved_url}')
            return []
        if response.status_code >= 400:
            self.logger.warning(f'CSS asset returned status {response.status_code}: {resolved_url}')
            return []

        content = response.text
        file_path: Optional[Path] = None
        if not self.no_download:
            file_path = self._save_css(resolved_url, content, output_dir)

        comments = self._extract_comments(content)
        variables = self._extract_variables(content)
        media_queries = self._extract_media_queries(content)
        selectors = self._extract_selectors(content)
        imports = self._parse_imports(content)

        css_info: Dict[str, Any] = {
            'url': resolved_url,
            'file_path': str(file_path) if file_path else None,
            'status_code': response.status_code,
            'comments': comments,
            'variables': variables,
            'media_queries': media_queries,
            'selectors': selectors,
            'content': content,
            'imports': imports,
        }

        nested_results: List[Dict[str, Any]] = []
        for import_url in imports:
            nested_results.extend(
                self._download_css_recursive(import_url, resolved_url, output_dir, depth - 1)
            )

        return [css_info] + nested_results

    def extract(
        self,
        css_urls: List[str],
        base_url: str,
        output_dir: Path,
    ) -> List[Dict[str, Any]]:
        """Download and parse external CSS assets."""
        results: List[Dict[str, Any]] = []
        if not css_urls:
            return results

        iterator = css_urls
        if self.logger:
            iterator = self.logger.progress(css_urls, desc='Downloading CSS')

        for css_url in iterator:
            results.extend(self._download_css_recursive(css_url, base_url, output_dir, self.max_depth))
        return results
