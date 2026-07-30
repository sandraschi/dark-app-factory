"""Tests for maps block."""
from __future__ import annotations
import pytest
@pytest.fixture(autouse=True)
def reset():
    from blocks.maps.backend import service as s
    s._locations.clear()

class TestMaps:
    def test_add_and_list(self):
        from blocks.maps.backend import service as s
        s.add_location("Store A", 48.2, 16.3, "Address 1")
        s.add_location("Store B", 48.3, 16.4, "Address 2", category="shop")
        assert len(s.list_locations()) == 2
        assert len(s.list_locations("shop")) == 1

    def test_nearby(self):
        from blocks.maps.backend import service as s
        s.add_location("Vienna Center", 48.208, 16.373)
        result = s.nearby(48.21, 16.37, 5)
        assert len(result) == 1
        assert result[0]["distance_km"] < 1
