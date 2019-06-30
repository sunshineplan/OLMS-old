import io

from setuptools import find_packages
from setuptools import setup

with io.open('README.rst', 'rt', encoding='utf8') as f:
    readme = f.read()

setup(
    name='OLMS',
    version='0.0.1',
    url='https://olms.shlib.cf',
    license='BSD',
    maintainer='Sunshine',
    maintainer_email='sunshineplan@gmail.com',
    description='Overtime and Leave Management System',
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['flask'],
)
