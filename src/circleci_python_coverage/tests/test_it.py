from unittest import TestCase, skipUnless
from sys import platform

from circleci_python_coverage import linux, windows, macos

class Tests(TestCase):

    @skipUnless("linux" in platform, "")
    def test_linux(self):
        linux.foo()

    @skipUnless("win32" in platform, "")
    def test_windows(self):
        windows.foo()

    @skipUnless("darwin" in platform, "")
    def test_macos(self):
        macos.foo()
