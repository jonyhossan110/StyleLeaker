from core.severity import SeverityScorer


def test_severity_scoring_generates_high_risk():
    scorer = SeverityScorer()
    analysis = {
        "hidden_fields": [{"name": "csrf_token", "value": "x"}],
        "sensitive_matches": ["admin-panel", "password-input"],
        "developer_notes": {"ip_addresses": ["10.0.0.2"], "notes": ["TODO"], "internal_urls": []},
        "versions": {"Bootstrap": "5.3.0"},
        "cdns": ["cloudflare"],
        "media_queries": ["(max-width: 768px)"],
        "css_variables": ["--color: #fff"],
    }
    recon_data = {
        "headers": {
            "findings": {
                "Server": {"status": "FAIL"},
                "X-Powered-By": {"status": "FAIL"},
            }
        }
    }
    result = scorer.score(analysis, recon_data=recon_data, js_data={"versions": {"jQuery": "3.7.1"}})

    assert result["overall_score"] > 0
    assert result["risk_level"] in {"HIGH", "CRITICAL"}
    assert len(result["findings_list"]) > 0
