from django.test import SimpleTestCase

from apps.dashboard.services import build_time_headers, validate_slot_indexes


class DashboardServicesTests(SimpleTestCase):
    def test_build_time_headers(self):
        self.assertEqual(
            build_time_headers(),
            ["10분", "20분", "30분", "40분", "50분", "60분"] * 2,
        )

    def test_validate_slot_indexes_accepts_valid_list(self):
        self.assertTrue(validate_slot_indexes([0, 1, 143]))

    def test_validate_slot_indexes_rejects_invalid_values(self):
        self.assertFalse(validate_slot_indexes([0, -1, 144]))
