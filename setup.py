from setuptools import setup, find_packages

setup(
    name="ans1meta",
    version="0.1.0",
    packages=find_packages(),
    description="A package that allows you to define metadata for ANS.1 types",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Alessandro Vecchi",
    license="MIT",
    url="https://github.com/veech/ans1meta",
    install_requires=[],
)
