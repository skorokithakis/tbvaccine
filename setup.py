#!/usr/bin/env python
import os.path
import sys
from itertools import chain

from setuptools import setup  # noqa
from setuptools.command.install_lib import install_lib

__version__ = ""  # Dummy version.
exec(open("tbvaccine/version.py").read())
assert sys.version >= "2.6", "Requires Python v2.6 or above."


class InstallLibWithPTH(install_lib):
    def run(self):
        install_lib.run(self)
        path = os.path.join(os.path.dirname(__file__), "tbvaccine.pth")
        dest = os.path.join(self.install_dir, os.path.basename(path))
        self.copy_file(path, dest)
        self.outputs = [dest]

    def get_outputs(self):
        return chain(install_lib.get_outputs(self), self.outputs)


classifiers = [
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.5",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

install_requires = ["pygments"]
tests_require = ["pep8", "pytest"] + install_requires

setup(
    name="tbvaccine",
    version=__version__,  # noqa
    author="Stavros Korokithakis",
    author_email="hi@stavros.io",
    url="https://github.com/skorokithakis/tbvaccine/",
    description="A utility that cures the horrible traceback displays in Python, " "making them more readable.",
    long_description=open("README.rst").read(),
    license="MIT",
    classifiers=classifiers,
    packages=["tbvaccine"],
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite="tbvaccine.tests",
    entry_points={"console_scripts": ["tbvaccine=tbvaccine.cli:main"]},
    cmdclass={"install_lib": InstallLibWithPTH},
)
