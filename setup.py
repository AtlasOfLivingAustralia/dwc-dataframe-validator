"""
Setup script for your dwc-dataframe-validator.
"""
from setuptools import setup

setup(
    name='dwc-dataframe-validator',
    version='0.1.1',
    author='Dave Martin',
    author_email='djtfmartin@gmail.com',
    packages=['dwc_validator'],
    url="https://github.com/djtfmartin/dwca-dataframe-validator",
    license='MPL 1.1',
    description='A simple Python package to validate darwin core data loaded into dataframes.',
    long_description='A simple Python package to validate darwin core data loaded into dataframes.',
    classifiers=[
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: Implementation :: PyPy',
    ]
)
