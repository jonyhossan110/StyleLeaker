from core.fetcher import Fetcher


def test_validate_url_accepts_http_and_https_only():
    fetcher = Fetcher()
    assert fetcher._validate_url("https://example.com") == "https://example.com"
    assert fetcher._validate_url("http://example.com") == "http://example.com"
    assert fetcher._validate_url("example.com") == "http://example.com"


def test_validate_url_rejects_unsupported_scheme():
    fetcher = Fetcher()
    try:
        fetcher._validate_url("ftp://example.com")
        raise AssertionError("Expected ValueError for unsupported scheme")
    except ValueError:
        pass


def test_parse_cookies_parses_pairs():
    fetcher = Fetcher()
    cookies = fetcher._parse_cookies("a=1; b=two")
    assert cookies == {"a": "1", "b": "two"}
