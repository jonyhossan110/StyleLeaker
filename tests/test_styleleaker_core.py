import json

from styleleaker import normalize_target_domain, parse_headers, positive_int


class DummyLogger:
    def __init__(self):
        self.errors = []

    def error(self, message):
        self.errors.append(message)


def test_positive_int_accepts_positive_values():
    assert positive_int("1") == 1
    assert positive_int("10") == 10


def test_positive_int_rejects_zero_and_negative():
    import argparse

    try:
        positive_int("0")
        raise AssertionError("Expected argparse.ArgumentTypeError")
    except argparse.ArgumentTypeError:
        pass

    try:
        positive_int("-3")
        raise AssertionError("Expected argparse.ArgumentTypeError")
    except argparse.ArgumentTypeError:
        pass


def test_normalize_target_domain_removes_port():
    assert normalize_target_domain("https://example.com:8443/path") == "example.com"


def test_parse_headers_accepts_json_object():
    logger = DummyLogger()
    parsed = parse_headers(json.dumps({"X-Test": "1"}), logger)
    assert parsed == {"X-Test": "1"}
    assert logger.errors == []


def test_parse_headers_rejects_invalid_json():
    logger = DummyLogger()
    parsed = parse_headers("{invalid}", logger)
    assert parsed is None
    assert logger.errors
