from setuptools import setup, find_packages
from os import path

# read the contents of the README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='datacockpit',
    version='0.2.0',
    author='Arpit Narechania',
    author_email='arpitnarechania@gatech.edu',
    packages=find_packages(),
    include_package_data=True,
    setup_requires=['pytest-runner'],
    test_requires=['pytest', 'pytest-cov'],
    scripts=[],
    url='https://github.com/datacockpit-org/datacockpit',
    license='LICENSE',
    description='DataCockpit is a package to analyze the usage and quality metrics of your database.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        "pandas>=1.4.0",
        "sql_metadata>=2.6.0",
        "sqlglot>=6.3.1",
        "sqlparse>=0.4.3",
        "sqlalchemy>=2.0.0"
    ]
)