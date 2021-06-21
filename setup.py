from setuptools import setup

setup(
    name='jp',
    version='0.1.0',
    py_modules=['jp'],
    install_requires=[
        'Click', "tabulate", "requests",
    ],
    entry_points={
        'console_scripts': [
            'jp = jp:cli',
        ],
    },
)
