from unittest import TestCase

from pyramid.request import Request

from pyramid_restler.util import get_param


class TestGetParam(TestCase):
    def test_flags(self):
        request = Request.blank("/endpoint?a&!b&c&c&!d&!d&e=&!f=")

        # Flag
        a = get_param(request, "a", bool)
        self.assertTrue(a)

        # Negated flag
        b = get_param(request, "b", bool)
        self.assertFalse(b)

        # Not a flag
        c = get_param(request, "c", bool, multi=True)
        self.assertEqual(c, [None, None])
        self.assertRaises(KeyError, get_param, request, "c", bool)

        # Also not a flag
        d = get_param(request, "!d", bool, multi=True)
        self.assertEqual(d, [None, None])
        self.assertRaises(KeyError, get_param, request, "d", bool)
        self.assertRaises(KeyError, get_param, request, "d", bool, multi=True)
        self.assertRaises(KeyError, get_param, request, "!d", bool)

        # Also not flags
        e = get_param(request, "e", bool)
        self.assertIsNone(e)

        f = get_param(request, "!f", bool)
        self.assertIsNone(f)
        self.assertRaises(KeyError, get_param, request, "f", bool)
