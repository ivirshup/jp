from setuptools import setup

setup(
    name='jp',
    version='0.2.0',
    py_modules=['jp'],
    install_requires=[
        'Click', "tabulate", "requests", "notebook>7"
    ],
    entry_points={
        'console_scripts': [
            'jp = jp:cli',
        ],
    },
)
