
import lib
import unittest

__author__ = 'User'

class BencodeDecoderTest(unittest.TestCase):

    def test_canReadInt(self):
        #lib.BencodeDecoder().readInt()
        self.assertEqual(1, 2, "not equal")

if __file__ == '__main__':
    unittest.main()
