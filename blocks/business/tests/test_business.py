"""Tests for business block."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset():
    from blocks.business.backend import service as s
    s._services.clear()
    s._faq.clear()
    s._contacts.clear()
    s._team.clear()
    s._next_service = 1
    s._next_faq = 1
    s._next_contact = 1


class TestBusinessInfo:
    def test_default_info(self):
        from blocks.business.backend import service as s
        info = s.get_info()
        assert "name" in info

    def test_update_info(self):
        from blocks.business.backend import service as s
        s.update_info({"name": "Test Biz", "phone": "555-0100"})
        assert s.get_info()["name"] == "Test Biz"


class TestServices:
    def test_add_and_list(self):
        from blocks.business.backend import service as s
        s.add_service("Consulting", "Expert advice", "$150/hr")
        s.add_service("Training", "Group sessions", category="education")
        assert len(s.list_services()) == 2
        assert len(s.list_services("education")) == 1

    def test_featured_service(self):
        from blocks.business.backend import service as s
        s.add_service("Premium", "Top tier", "$500", featured=True)
        assert s.list_services()[0]["featured"] is True


class TestFaq:
    def test_add_and_list(self):
        from blocks.business.backend import service as s
        s.add_faq("Q1?", "A1")
        s.add_faq("Q2?", "A2", category="billing")
        assert len(s.list_faq()) == 2
        assert len(s.list_faq("billing")) == 1


class TestContact:
    def test_submit(self):
        from blocks.business.backend import service as s
        c = s.submit_contact("Alice", "a@b.com", "555", "Help!")
        assert c["name"] == "Alice"
        assert c["read"] is False


class TestTeam:
    def test_add_and_list(self):
        from blocks.business.backend import service as s
        s.add_team_member("Bob", "Technician", "Expert")
        members = s.list_team()
        assert len(members) == 1
        assert members[0]["name"] == "Bob"
