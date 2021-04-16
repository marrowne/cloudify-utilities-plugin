import unittest

from ..ip_reservation import IpReservation


class TestTasks(unittest.TestCase):
    def test_constructor_type_error(self):
        available = {'127.0.0.1'}
        with self.assertRaises(TypeError):
            IpReservation(available)

    def test_reserve_ip(self):
        ip_reservation = IpReservation([])
        result = ip_reservation.reserve('127.0.0.1')

        self.assertTrue(result)

    def test_reserve_ipv6(self):
        ip_reservation = IpReservation()
        result = ip_reservation.reserve('2001:db8::1000')

        self.assertTrue(result)
        self.assertFalse(ip_reservation.is_free('2001:db8::1000'))

    def test_reserved_ip(self):
        ip_reservation = IpReservation()
        ip_reservation.reserve('127.0.0.1')
        result = ip_reservation.reserve('127.0.0.1')

        self.assertFalse(result)

    def test_reserved_ipv6(self):
        ip_reservation = IpReservation()
        ip_reservation.reserve('2001:db8::1000')
        result = ip_reservation.reserve('2001:db8::1000')

        self.assertFalse(result)

    def test_free_ip(self):
        available = ['1.1.1.0/24']
        ip_reservation = IpReservation(available)

        ip_reservation.free('127.0.0.1')

        self.assertTrue(ip_reservation.is_free('127.0.0.1'))

    def test_free_range(self):
        available = ['1.1.1.0/24']
        ip_reservation = IpReservation(available)

        ip_reservation.free_range('10.0.0.1', '10.0.0.10')

        self.assertTrue(ip_reservation.is_free('10.0.0.1'))
        self.assertTrue(ip_reservation.is_free('10.0.0.5'))
        self.assertTrue(ip_reservation.is_free('10.0.0.10'))

    def test_free_ipv6(self):
        available = ['2001:db8:100::/40']
        ip_reservation = IpReservation(available)

        ip_reservation.free('2001:db8::1000')

        self.assertTrue(ip_reservation.is_free('2001:db8::1000'))

    def test_reserve_ipv4_range(self):
        ip_reservation = IpReservation()
        result = ip_reservation.reserve_range('10.0.0.1', '10.0.0.10')

        self.assertTrue(result)

    def test_reserve_ipv6_range(self):
        ip_reservation = IpReservation()
        result = ip_reservation.reserve_range('2001:db8::1000',
                                              '2001:db8::2000')

        self.assertTrue(result)

    def test_reserve_unavailable_ipv6_range(self):
        available = ['2001:db8::1000/116', '2001:db8:100::/40']
        ip_reservation = IpReservation(available)
        result = ip_reservation.reserve_range('2001:db8::1000',
                                              '2001:db8::2000')

        self.assertFalse(result)
        self.assertEqual(ip_reservation.available_ipv6, available)

    def test_reserve_mixed_range_error(self):
        ip_reservation = IpReservation()

        with self.assertRaises(TypeError):
            ip_reservation.reserve_range('10.0.0.1', '2001:db8::1000')

    def test_reserved_range(self):
        available = ['192.2.0.0/15']
        ip_reservation = IpReservation(available)
        result = ip_reservation.is_range_free('192.0.2.0', '192.0.2.130')
        self.assertFalse(result)

    def test_consolidate(self):
        available = ['0.0.0.0/1', '128.0.0.0/1']
        ip_reservation = IpReservation(available)
        ip_reservation.collapse_addresses()
        self.assertEqual(len(ip_reservation.available_ipv4), 1)
