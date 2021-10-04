# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
# from pip.req import parse_requirements
import re, ast

# get version from __version__ variable in angola_erp/__init__.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('angola_erp/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

# requirements = parse_requirements("requirements.txt", session="")

setup(
	name='angola_erp',
	version=version,
	description='Angola ERPNEXT extensao',
	author='Helio de Jesus',
	author_email='hcesar@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=['frappe']
)
