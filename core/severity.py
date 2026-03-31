from __future__ import annotations

from typing import Any, Dict, List, Optional


class SeverityScorer:
    """Severity scoring system for StyleLeaker findings."""

    CRITICAL_TOKENS = ['token', 'csrf', 'key']
    HIGH_PATTERNS = ['admin', 'password', 'payment']

    def score(
        self,
        analysis: Dict[str, Any],
        recon_data: Optional[Dict[str, Any]] = None,
        js_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compute severity scores and build a sorted findings summary."""
        hidden_fields = analysis.get('hidden_fields', [])
        sensitive_matches = analysis.get('sensitive_matches', [])
        developer_notes = analysis.get('developer_notes', {})
        versions = analysis.get('versions', {})
        cdns = analysis.get('cdns', [])
        media_queries = analysis.get('media_queries', [])
        css_variables = analysis.get('css_variables', [])

        critical_hidden = [
            item for item in hidden_fields
            if any(token in item.get('name', '').lower() for token in self.CRITICAL_TOKENS)
        ]
        high_sensitive = [
            item for item in sensitive_matches
            if any(pattern in item.lower() for pattern in self.HIGH_PATTERNS)
        ]
        ip_addresses = developer_notes.get('ip_addresses', [])
        todo_notes = developer_notes.get('notes', [])
        js_versions = js_data.get('versions', {}) if js_data else {}
        version_count = len(versions) + len(js_versions)
        header_leaks = self._count_header_leaks(recon_data)

        score = min(
            100,
            len(critical_hidden) * 30
            + len(high_sensitive) * 18
            + len(ip_addresses) * 18
            + len(todo_notes) * 8
            + version_count * 10
            + len(cdns) * 3
            + len(media_queries) * 2
            + len(css_variables) * 1
            + header_leaks * 5,
        )

        if score >= 70:
            risk_level = 'CRITICAL'
        elif score >= 40:
            risk_level = 'HIGH'
        elif score >= 20:
            risk_level = 'MEDIUM'
        elif score > 0:
            risk_level = 'LOW'
        else:
            risk_level = 'INFO'

        findings: List[Dict[str, Any]] = []
        self._append_finding(findings, 'Hidden fields with token/csrf/key', 'CRITICAL', len(critical_hidden))
        self._append_finding(findings, 'High-risk sensitive class/ID patterns', 'HIGH', len(high_sensitive))
        self._append_finding(findings, 'Internal IP addresses in comments', 'HIGH', len(ip_addresses))
        self._append_finding(findings, 'Exposed header leaks', 'HIGH', header_leaks)
        self._append_finding(findings, 'Developer TODO/FIXME notes', 'MEDIUM', len(todo_notes))
        self._append_finding(findings, 'Detected framework versions', 'MEDIUM', version_count)
        self._append_finding(findings, 'CDN usage detected', 'LOW', len(cdns))
        self._append_finding(findings, 'CSS media query breakpoints', 'LOW', len(media_queries))
        self._append_finding(findings, 'CSS variables extracted', 'INFO', len(css_variables))

        findings = [item for item in findings if item['count'] > 0]
        findings.sort(key=self._severity_sort_key)

        return {
            'overall_score': score,
            'risk_level': risk_level,
            'findings_list': findings,
            'critical_hidden': len(critical_hidden),
            'high_sensitive': len(high_sensitive),
            'ip_addresses': len(ip_addresses),
            'developer_notes': len(todo_notes),
            'version_detections': version_count,
        }

    def _count_header_leaks(self, recon_data: Optional[Dict[str, Any]]) -> int:
        if not recon_data:
            return 0
        headers = recon_data.get('headers', {}).get('findings', {})
        leaks = 0
        for name, details in headers.items():
            if details.get('status') == 'FAIL':
                leaks += 1
        return leaks

    def _append_finding(self, findings: List[Dict[str, Any]], finding: str, severity: str, count: int) -> None:
        findings.append({
            'finding': finding,
            'severity': severity,
            'count': count,
        })

    def _severity_sort_key(self, item: Dict[str, Any]) -> int:
        order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        return order.get(item.get('severity', 'INFO'), 4)
