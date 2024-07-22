import pytest
from sharh.parser import parse, ParseError

def test_string_identifier_eq():
    tree = parse("http.headers.user_agent == 'curl/8.1-beta'")

    assert tree.to_expr_notation() == ["http.headers.user_agent", "==", "curl/8.1-beta"]

    # with space
    tree = parse("http.headers.user_agent == 'curl/8.1-beta test'")
    assert tree.to_expr_notation() == ["http.headers.user_agent", "==", "curl/8.1-beta test"]

def test_string_identifier_neq():
    tree = parse("http.headers.user_agent != 'curl/8.1-beta'")

    assert tree.to_expr_notation() == ["http.headers.user_agent", "~=", "curl/8.1-beta"]

def test_string_identifer_contains():
    tree = parse("http.headers.user_agent contains 'curl/8.1-beta'")

    assert tree.to_expr_notation() == ["http.headers.user_agent", "~~", "curl/8.1-beta"]

def test_string_identifier_not_contains():
    tree = parse("http.headers.user_agent not contains 'curl/8.1-beta'")

    assert tree.to_expr_notation() == ["http.headers.user_agent", "!", "~~", "curl/8.1-beta"]

def test_string_identifier_in():
    tree = parse("http.headers.user_agent in [ 'curl', 'firefox'  ,'chrome'  ]")
    assert tree.to_expr_notation() == ["http.headers.user_agent", "in", ['curl', 'firefox', 'chrome']]

def test_string_identifier_not_in():
    tree = parse("http.headers.user_agent not in ['curl' ,'firefox',  'chrome' ]")
    assert tree.to_expr_notation() == ["http.headers.user_agent", "!", "in", ['curl', 'firefox', 'chrome']]

def test_string_identifier_dont_support_has():
    with pytest.raises(ParseError):
        parse("http.headers.user_agent has 'curl/8.1-beta'")

def test_custom_header():
    tree = parse("http.headers['content-type'] == 'text/html'")

    assert tree.to_expr_notation() == ["http.headers['content-type']", "==", "text/html"]

def test_list_identifier_has():
    tree = parse("http.headers has 'test-key'")

    assert tree.to_expr_notation() == ["http.headers", "has", "test-key"]

def test_list_identifier_has_not():
    tree = parse("http.headers not has 'test-key'")

    assert tree.to_expr_notation() == ["http.headers", "!", "has", "test-key"]

def test_asn():
    tree = parse("ip.geoip.asn == 1234")

    assert tree.to_expr_notation() == ["ip.geoip.asn", "==", "1234"]

def test_asn_invalid():
    with pytest.raises(ParseError):
        parse("ip.geoip.asn == '1234'")

def test_asn_in():
    tree = parse("ip.geoip.asn in [  1234 , 345 ]")
    assert tree.to_expr_notation() == ["ip.geoip.asn", "in", ["1234", "345"]]

def test_ip():
    tree = parse("ip.addr == 127.0.0.1")

    assert tree.to_expr_notation() == ["ip.addr", "==", "127.0.0.1"]

def test_ip_invalid():
    with pytest.raises(ParseError):
        parse("ip.addr == 256.1.1.1")

def test_ip_in():
    tree = parse("ip.addr in [ 192.168.1.1/28   ,  127.0.0.1 ]")

    assert tree.to_expr_notation() == ["ip.addr", "ipmatch", ["192.168.1.1/28", "127.0.0.1"]]

def test_ip_not_in():
    tree = parse("ip.addr not in [192.168.1.1/28, 127.0.0.1]")

    assert tree.to_expr_notation() == ["ip.addr", "!", "ipmatch", ["192.168.1.1/28", "127.0.0.1"]]

def test_boolean_variables():
    tree = parse("http.secure == 'on'")
    assert tree.to_expr_notation() == ["http.secure", "==", True]

    tree = parse("http.secure == 'off'")
    assert tree.to_expr_notation() == ["http.secure", "==", False]

    with pytest.raises(ParseError):
        parse("http.secure != 'off")

    with pytest.raises(ParseError):
        parse("http.secure == 'invalid value")


def test_multiple():
    tree = parse("http.headers.user_agent != 'curl' and ip.addr == 127.0.0.1")

    assert tree.to_expr_notation() == ["AND", ["http.headers.user_agent", "~=", "curl"], ["ip.addr", "==", "127.0.0.1"]]
