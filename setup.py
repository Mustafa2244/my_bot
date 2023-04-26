from setuptools import setup, find_packages
import sys

setup(
    name='my_bot',                    # package name
    version='0.1',                    # version
    description='Command line bot',    # short description
    install_requires=[                # list of packages this package depends
        "fuzzywuzzy",
        "python-Levenshtein"
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'my-bot=my_bot.bot:main',
        ],
    }
)
