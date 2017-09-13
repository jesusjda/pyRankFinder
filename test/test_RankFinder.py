import unittest
import rankfinder
import genericparser
import lpi
import termination

class TestKey(unittest.TestCase):
    def test_import(self):
        self.assertEqual(1, 1)

    def test_ppl(self):
        lpi.C_Polyhedron(lplib="ppl")
        self.assertEqual(1, 1)

    def test_z3(self):
        try:
            lpi.C_Polyhedron(lplib="z3")
        except NotImplementedError as e:
            self.skipTest("z3 is not implemented")
        self.assertEqual(1, 1)
