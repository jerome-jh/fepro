import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "logic",
    version = "0.0.1",
    author = "jerome-jh",
    author_email = "github",
    description = ("Transform boolean equation to Conjunctive Normal Form"),
    license = "GPLv3",
    keywords = "logic boolean equation CNF",
    url = "https://github.com/jerome-jh/fepro",
    packages=['test'],
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPLv3 License",
    ],
    python_requires='>=3.5',
    test_suite="test.test"
)
