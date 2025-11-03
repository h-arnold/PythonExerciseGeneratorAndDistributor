"""
Tests for the example hello exercise
"""
from exercises.example_hello import greet


def test_greet_world():
    """Test greeting World"""
    assert greet("World") == "Hello, World!"


def test_greet_custom_name():
    """Test greeting with a custom name"""
    assert greet("Alice") == "Hello, Alice!"


def test_greet_empty_string():
    """Test greeting with empty string"""
    assert greet("") == "Hello, !"
