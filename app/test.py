#Use this command to run: py.test --verbose --junit-xml data/result.xml test.py
import unittest

class TestRps(unittest.TestCase):
    """
    Dummy test case
    """
    def test_dummy(self):
        """
        Always pass
        """
        pass
    """
    Dummy test case
    """
    def test_dummy_2(self):
        """
        Always pass
        """
        pass


if __name__ == '__main__':
    unittest.main()
