import pytest
from sharh.parser import parse, ParseError
from sharh.expr import Literal

def test_string_identifier_eq():
    tree = parse("http.headers.user_agent == 'curl/8.1-beta'")

    assert tree.to_expr_notation() == ["http_user_agent", "==", "curl/8.1-beta"]

    # with space
    tree = parse("http.headers.user_agent == 'curl/8.1-beta test'")
    assert tree.to_expr_notation() == ["http_user_agent", "==", "curl/8.1-beta test"]

def test_string_identifier_neq():
    tree = parse("http.headers.user_agent != 'curl/8.1-beta'")

    assert tree.to_expr_notation() == ["http_user_agent", "~=", "curl/8.1-beta"]

def test_string_identifer_contains():
    tree = parse("http.headers.user_agent contains 'curl/8.1-beta'")

    assert tree.to_expr_notation() == ["http_user_agent", "~~", "curl/8.1-beta"]

def test_string_identifier_not_contains():
    tree = parse("http.headers.user_agent !contains 'curl/8.1-beta'")

    assert tree.to_expr_notation() == ["http_user_agent", "!", "~~", "curl/8.1-beta"]

def test_string_identifier_in():
    tree = parse("http.headers.user_agent in [ 'curl', 'firefox'  ,'chrome'  ]")
    assert tree.to_expr_notation() == ["http_user_agent", "in", ['curl', 'firefox', 'chrome']]

def test_string_identifier_not_in():
    tree = parse("http.headers.user_agent !in ['curl' ,'firefox',  'chrome' ]")
    assert tree.to_expr_notation() == ["http_user_agent", "!", "in", ['curl', 'firefox', 'chrome']]

def test_string_identifier_dont_support_has():
    with pytest.raises(ParseError):
        parse("http.headers.user_agent has 'curl/8.1-beta'")

def test_custom_header():
    tree = parse("http.headers['content-type'] == 'text/html'")

    assert tree.to_expr_notation() == ["http_content_type", "==", "text/html"]

def test_list_identifier_has():
    tree = parse("http.headers has 'test-key'")

    assert tree.to_expr_notation() == ["headers", "has", "test-key"]

def test_list_identifier_has_not():
    tree = parse("http.headers !has 'test-key'")

    assert tree.to_expr_notation() == ["headers", "!", "has", "test-key"]

def test_asn():
    tree = parse("ip.geoip.asn == 1234")

    assert tree.to_expr_notation() == ["geoip2_data_asn", "==", "1234"]

def test_asn_invalid():
    with pytest.raises(ParseError):
        parse("ip.geoip.asn == '1234'")

def test_asn_in():
    tree = parse("ip.geoip.asn in [  1234 , 345 ]")
    assert tree.to_expr_notation() == ["geoip2_data_asn", "in", ["1234", "345"]]

def test_ip_reputation_ge():
    tree = parse("ip.reputation >= 10")

    assert tree.to_expr_notation() == ["ip.reputation", ">=", "10"]

def test_ip_reputation_le():
    tree = parse("ip.reputation <= 10")

    assert tree.to_expr_notation() == ["ip.reputation", "<=", "10"]

def test_ip():
    tree = parse("ip.addr == 127.0.0.1")

    assert tree.to_expr_notation() == ["remote_addr", "==", "127.0.0.1"]

def test_ip_invalid():
    with pytest.raises(ParseError):
        parse("ip.addr == 256.1.1.1")

def test_ip_in():
    tree = parse("ip.addr in [ 192.168.1.1/28   ,  127.0.0.1 ]")

    assert tree.to_expr_notation() == ["remote_addr", "ipmatch", ["192.168.1.1/28", "127.0.0.1"]]

def test_ip_not_in():
    tree = parse("ip.addr !in [192.168.1.1/28, 127.0.0.1]")

    assert tree.to_expr_notation() == ["remote_addr", "!", "ipmatch", ["192.168.1.1/28", "127.0.0.1"]]

def test_boolean_variables():
    tree = parse("http.secure == true")
    assert tree.to_expr_notation() == ["scheme", "==", "https"]

    tree = parse("http.secure == false")
    assert tree.to_expr_notation() == ["scheme", "==", "http"]

    with pytest.raises(ParseError):
        parse("http.secure == 'invalid value")


def test_multiple():
    tree = parse("http.headers.user_agent != 'curl' and ip.addr == 127.0.0.1")

    assert tree.to_expr_notation() == ["AND", ["http_user_agent", "~=", "curl"], ["remote_addr", "==", "127.0.0.1"]]


def test_custom_literal_classes_override_lvalue():
    tree = parse("http.headers.referer == 'https://github.com'")

    assert tree.to_expr_notation() == ["http_referer", "==", "https://github.com"]

    class CustomReferer(Literal):
        def get_lvalue(self):
            return "custom_header"

    tree = parse("http.headers.referer == 'https://github.com'", {"http.headers.referer": CustomReferer})

    assert tree.to_expr_notation() == ["custom_header", "==", "https://github.com"]

def test_custom_literal_classes_override_and_add_validation():
    tree = parse("ip.reputation == 1000")

    assert tree.to_expr_notation() == ["ip.reputation", "==", "1000"]

    class CustomReputation(Literal):
        def __init__(self, left, op, right):
            print(int(right))
            if int(right) > 100 or int(right) < 1:
                raise ParseError

            super().__init__(left, op, right)

        def get_lvalue(self):
            return "reputation"

        def get_rvalue(self):
            return int(self.right)

    with pytest.raises(ParseError):
        tree = parse("ip.reputation >= 101", {"ip.reputation": CustomReputation})

    with pytest.raises(ParseError):
        tree = parse("ip.reputation >= 101", {"ip.reputation": CustomReputation})

    tree = parse("ip.reputation >= 50", {"ip.reputation": CustomReputation})

    assert tree.to_expr_notation() == ["reputation", ">=", 50]
