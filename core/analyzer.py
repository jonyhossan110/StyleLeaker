from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

SENSITIVE_PATTERNS = [
    'admin', 'login', 'logout', 'dashboard', 'panel',
    'config', 'setup', 'install', 'debug', 'test',
    'backup', 'secret', 'private', 'internal', 'api',
    'password', 'token', 'auth', 'user', 'account',
    'payment', 'billing', 'invoice', 'cart', 'checkout',
    'upload', 'file', 'download', 'export', 'import',
    'database', 'db', 'sql', 'query', 'dev', 'staging',
]

FRAMEWORK_SIGNATURES = {
    'Bootstrap': ['bootstrap', '.container', '.row', '.col-'],
    'Tailwind': ['tailwind', 'tw-', 'sm:', 'md:', 'lg:', 'xl:', '2xl:'],
    'Foundation': ['foundation'],
    'Bulma': ['bulma'],
    'WordPress': ['wp-content', 'wp-includes'],
    'Drupal': ['drupal', 'sites/all'],
    'Joomla': ['joomla', 'components/com_'],
}

CDN_KEYWORDS = ['cdnjs', 'jsdelivr', 'unpkg', 'googleapis', 'stackpath', 'cloudflare']
VERSION_PATTERN = re.compile(r'([\w-]+)(?:@|[-_/])([0-9]+(?:\.[0-9]+)+)')
IP_PATTERN = re.compile(r'(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)')
INTERNAL_URL_PATTERN = re.compile(r'https?://(?:192\.168\.|10\.|127\.|172\.(?:1[6-9]|2\d|3[0-1])\.)[\w\-\./:]*', re.IGNORECASE)
DEV_NOTE_PATTERN = re.compile(r'\b(TODO|FIXME|credential|password|secret|api[_-]?key|token|internal)\b', re.IGNORECASE)


class Analyzer:
    """Analysis engine for sensitive patterns and framework fingerprinting."""

    def analyze(
        self,
        html_data: Dict[str, Any],
        css_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Perform security and framework analysis based on parsed HTML and CSS."""
        sensitive_matches = self._find_sensitive_html_patterns(html_data)
        frameworks = self._detect_frameworks(html_data, css_data)
        versions = self._detect_versions(css_data)
        cdns = self._detect_cdns(html_data, css_data)
        developer_notes = self._scan_developer_comments(html_data, css_data)

        hidden_fields = self._find_hidden_inputs(html_data)
        css_variables = self._collect_css_variables(css_data)
        media_queries = self._collect_media_queries(css_data)
        html_comments = html_data.get('comments', [])
        css_comments = self._collect_css_comments(css_data)

        return {
            'sensitive_matches': sorted(sensitive_matches),
            'frameworks': frameworks,
            'versions': versions,
            'cdns': sorted(cdns),
            'developer_notes': developer_notes,
            'hidden_fields': hidden_fields,
            'css_variables': sorted(set(css_variables)),
            'media_queries': sorted(set(media_queries)),
            'html_comments': html_comments,
            'css_comments': css_comments,
            'total_css_files': len(css_data),
            'total_inline_styles': len(html_data.get('inline_styles', [])),
        }

    def _find_sensitive_html_patterns(self, html_data: Dict[str, Any]) -> Set[str]:
        found: Set[str] = set()
        for value in html_data.get('class_names', []) + html_data.get('id_names', []):
            lower = value.lower()
            for pattern in SENSITIVE_PATTERNS:
                if pattern in lower:
                    found.add(value)
        return found

    def _detect_frameworks(self, html_data: Dict[str, Any], css_data: List[Dict[str, Any]]) -> List[str]:
        detected: Set[str] = set()
        for css_entry in css_data:
            url = css_entry.get('url', '').lower()
            content = css_entry.get('content', '').lower()
            for framework, signatures in FRAMEWORK_SIGNATURES.items():
                for signature in signatures:
                    if signature in url or signature in content:
                        detected.add(framework)
                        break
        for script_url in html_data.get('script_sources', []):
            lower = script_url.lower()
            if 'jquery' in lower and 'wordpress' in lower:
                detected.add('WordPress')
        return sorted(detected)

    def _detect_versions(self, css_data: List[Dict[str, Any]]) -> Dict[str, str]:
        versions: Dict[str, str] = {}
        for css_entry in css_data:
            url = css_entry.get('url', '')
            for match in VERSION_PATTERN.findall(url):
                framework, version = match
                framework_name = framework.capitalize()
                versions[framework_name] = version
        return versions

    def _detect_cdns(self, html_data: Dict[str, Any], css_data: List[Dict[str, Any]]) -> Set[str]:
        cdns: Set[str] = set()
        urls = html_data.get('stylesheet_links', []) + html_data.get('script_sources', [])
        for css_entry in css_data:
            urls.append(css_entry.get('url', ''))
        for url in urls:
            lower = url.lower()
            for keyword in CDN_KEYWORDS:
                if keyword in lower:
                    cdns.add(keyword)
        return cdns

    def _scan_developer_comments(self, html_data: Dict[str, Any], css_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        todo_fixme: Set[str] = set()
        ip_addresses: Set[str] = set()
        internal_urls: Set[str] = set()

        for comment in html_data.get('comments', []):
            self._scan_comment_text(comment, todo_fixme, ip_addresses, internal_urls)
        for css_entry in css_data:
            for comment in css_entry.get('comments', []):
                self._scan_comment_text(comment, todo_fixme, ip_addresses, internal_urls)

        return {
            'notes': sorted(todo_fixme),
            'ip_addresses': sorted(ip_addresses),
            'internal_urls': sorted(internal_urls),
        }

    def _scan_comment_text(self, content: str, todo_fixme: Set[str], ip_addresses: Set[str], internal_urls: Set[str]) -> None:
        for match in DEV_NOTE_PATTERN.findall(content):
            todo_fixme.add(match)
        for ip in IP_PATTERN.findall(content):
            ip_addresses.add(ip)
        for internal in INTERNAL_URL_PATTERN.findall(content):
            internal_urls.add(internal)

    def _find_hidden_inputs(self, html_data: Dict[str, Any]) -> List[Dict[str, str]]:
        hidden_fields: List[Dict[str, str]] = []
        for form in html_data.get('forms', []):
            for field in form.get('fields', []):
                if field.get('type') == 'hidden':
                    entry = {
                        'action': form.get('action', ''),
                        'name': field.get('name', ''),
                        'value': field.get('value', ''),
                    }
                    hidden_fields.append(entry)
        return hidden_fields

    def _collect_css_variables(self, css_data: List[Dict[str, Any]]) -> List[str]:
        variables: List[str] = []
        for css_entry in css_data:
            variables.extend(css_entry.get('variables', []))
        return variables

    def _collect_media_queries(self, css_data: List[Dict[str, Any]]) -> List[str]:
        breakpoints: List[str] = []
        for css_entry in css_data:
            breakpoints.extend(css_entry.get('media_queries', []))
        return breakpoints

    def _collect_css_comments(self, css_data: List[Dict[str, Any]]) -> List[str]:
        comments: List[str] = []
        for css_entry in css_data:
            comments.extend(css_entry.get('comments', []))
        return comments
