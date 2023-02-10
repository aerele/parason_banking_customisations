from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in parason_banking_customisations/__init__.py
from parason_banking_customisations import __version__ as version

setup(
	name="parason_banking_customisations",
	version=version,
	description="Customisations related to Bank Integrations for Parason",
	author="Aerele Technologies Private Limited",
	author_email="hello@aerele.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
