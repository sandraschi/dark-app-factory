"""Tests for membership block."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_db():
    from blocks.membership.backend import models as m

    m._memory_db["members"].clear()
    m._memory_db["customers"].clear()
    m._memory_db["employees"].clear()
    for k in m._next_ids:
        m._next_ids[k] = 1


class TestMemberAuth:
    def test_create_member(self):
        from blocks.membership.backend.auth import hash_password
        from blocks.membership.backend import models as m

        hashed = hash_password("secret123")
        member = m.create_member("alice@test.com", hashed, "Alice")
        assert member["email"] == "alice@test.com"
        assert "password_hash" not in member  # never exposed

    def test_list_members(self):
        from blocks.membership.backend.auth import hash_password
        from blocks.membership.backend import models as m

        m.create_member("a@t.com", hash_password("x"), "A", role="member")
        m.create_member("b@t.com", hash_password("x"), "B", role="admin")
        assert len(m.list_members()) == 2
        assert len(m.list_members(role="admin")) == 1

    def test_member_status_filter(self):
        from blocks.membership.backend.auth import hash_password
        from blocks.membership.backend import models as m

        m.create_member("a@t.com", hash_password("x"), "A")
        member = m.get_member_by_id(1)
        m.update_member(1, {"status": "inactive"})
        assert len(m.list_members(status="active")) == 0
        assert len(m.list_members(status="inactive")) == 1


class TestCustomer:
    def test_create_and_list(self):
        from blocks.membership.backend import models as m

        m.create_customer("cust@test.com", "Customer Inc", company="ACME", created_by=1)
        assert len(m.list_customers()) == 1
        assert len(m.list_customers(search="acme")) == 1

    def test_search(self):
        from blocks.membership.backend import models as m

        m.create_customer("a@x.com", "Alice")
        m.create_customer("b@x.com", "Bob")
        assert len(m.list_customers(search="alice")) == 1


class TestEmployee:
    def test_create_and_filter(self):
        from blocks.membership.backend import models as m

        m.create_employee("eng@test.com", "Engineer", department="Engineering", position="Dev")
        m.create_employee("mkt@test.com", "Marketer", department="Marketing", position="Lead")
        assert len(m.list_employees()) == 2
        assert len(m.list_employees(department="Engineering")) == 1

    def test_get_employee(self):
        from blocks.membership.backend import models as m

        m.create_employee("e@t.com", "E", department="Eng")
        e = m.get_employee(1)
        assert e is not None
        assert e["name"] == "E"


class TestAuth:
    def test_password_hashing(self):
        from blocks.membership.backend.auth import hash_password, verify_password

        h = hash_password("mypass")
        assert verify_password("mypass", h)
        assert not verify_password("wrong", h)

    def test_token_roundtrip(self):
        from blocks.membership.backend.auth import create_token, decode_token

        token = create_token(1, "admin")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["role"] == "admin"
