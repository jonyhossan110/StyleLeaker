from __future__ import annotations

import re
from typing import Any, Dict, List

VERSION_PATTERN = re.compile(r'([\w-]+)(?:@|[-_/])([0-9]+(?:\.[0-9]+)+)')
JS_FRAMEWORK_PATTERNS = {
    'jQuery': ['jquery'],
    'React': ['react'],
    'Vue': ['vue.js', '/vue', 'vue@', 'vue-'],
    'Angular': ['angular', 'angularjs'],
    'Alpine.js': ['alpine.js', 'alpinejs', 'x-data'],
    'HTMX': ['htmx', 'htmx.org'],
}


class JSCrossRef:
    """Cross-reference JavaScript sources with CSS findings."""

    def analyze(self, html_data: Dict[str, Any], css_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze JS URLs and correlate with CSS framework findings."""
        script_urls = sorted(set(html_data.get('script_sources', [])))
        libraries: List[str] = []
        versions: Dict[str, str] = {}

        for script_url in script_urls:
            lower_url = script_url.lower()
            for library, patterns in JS_FRAMEWORK_PATTERNS.items():
                if any(pattern in lower_url for pattern in patterns):
                    if library not in libraries:
                        libraries.append(library)
                    version = self._extract_version(script_url)
                    if version and library not in versions:
                        versions[library] = version
                    break

        correlations = self._correlate_with_css(script_urls, css_data, libraries)

        return {
            'script_urls': script_urls,
            'libraries': libraries,
            'versions': versions,
            'correlations': correlations,
        }

    def _extract_version(self, url: str) -> str:
        match = VERSION_PATTERN.search(url)
        if match:
            return match.group(2)
        return ''

    def _correlate_with_css(
        self,
        script_urls: List[str],
        css_data: List[Dict[str, Any]],
        libraries: List[str],
    ) -> List[str]:
        correlations: List[str] = []
        css_urls = [entry.get('url', '').lower() for entry in css_data]

        if any('bootstrap' in url for url in css_urls) and 'jQuery' in libraries:
            correlations.append('Bootstrap + jQuery')
        if any('tailwind' in url for url in css_urls) and 'Alpine.js' in libraries:
            correlations.append('Tailwind + Alpine.js')
        if any('bulma' in url for url in css_urls) and 'Vue' in libraries:
            correlations.append('Bulma + Vue')
        if any('foundation' in url for url in css_urls) and 'jQuery' in libraries:
            correlations.append('Foundation + jQuery')
        if any('wp-content' in url for url in css_urls) and 'jQuery' in libraries:
            correlations.append('WordPress + jQuery')

        return sorted(set(correlations))
