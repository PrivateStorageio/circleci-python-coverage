from unittest import TestCase

from circleci_python_coverage import foo

class Tests(TestCase):
    def test_foo(self):
        foo()
