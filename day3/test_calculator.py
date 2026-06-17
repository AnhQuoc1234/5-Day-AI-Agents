import pytest
from calculator import add, subtract, multiply, divide

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(-5, -5) == -10
    assert add(0.1, 0.2) == pytest.approx(0.3)

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(1, 5) == -4
    assert subtract(-5, -5) == 0

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6
    assert multiply(0, 5) == 0

def test_divide():
    assert divide(6, 3) == 2
    assert divide(5, 2) == 2.5
    assert divide(-6, 3) == -2
    
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        divide(5, 0)
