import unittest
import termination
import genericparser
import lpi
import termination.TerminationResult


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

    def test_Result(self):
        r = termination.Result(status=termination.TerminationResult.TERMINATE)
        self.assertTrue(r.get_status().is_terminate())
