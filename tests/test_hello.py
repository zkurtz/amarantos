from amarantos import hello


def test_hello():
    result = hello()
    assert "amarantos" in result
    assert "long and healthy life" in result
