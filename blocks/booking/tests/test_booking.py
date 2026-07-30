"""Tests for booking block."""
from __future__ import annotations
import pytest
@pytest.fixture(autouse=True)
def reset():
    from blocks.booking.backend import service as s
    s._appointments.clear(); s._next_id = 1

class TestBooking:
    def test_get_slots(self):
        from blocks.booking.backend import service as s
        slots = s.get_available_slots()
        assert len(slots) > 0

    def test_create_appointment(self):
        from blocks.booking.backend import service as s
        a = s.create_appointment("2026-08-01T10:00:00", "Alice", "a@b.com")
        assert a["customer_name"] == "Alice"
        assert a["status"] == "confirmed"

    def test_list_appointments(self):
        from blocks.booking.backend import service as s
        s.create_appointment("2026-08-01T10:00:00", "A", "a@b.com")
        s.create_appointment("2026-08-01T11:00:00", "B", "b@b.com")
        assert len(s.list_appointments()) == 2

    def test_cancel_appointment(self):
        from blocks.booking.backend import service as s
        s.create_appointment("2026-08-01T10:00:00", "A", "a@b.com")
        s.update_appointment(1, {"status": "cancelled"})
        assert len(s.list_appointments("cancelled")) == 1

    def test_slot_availability(self):
        from blocks.booking.backend import service as s
        s.create_appointment("2026-08-01T10:00:00", "A", "a@b.com")
        assert s.get_appointment(1) is not None

    def test_appointment_not_found(self):
        from blocks.booking.backend import service as s
        assert s.get_appointment(999) is None
