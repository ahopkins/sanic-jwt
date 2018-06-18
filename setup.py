from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

tests_require = [
    "coverage",
    "freezegun",
    # 'pytest-cache',
    "pytest-cov",
    "pytest-flakes",
    "pytest-pep8",
    # 'pytest-sanic',
    "pytest-asyncio",
    "pytest",
    "sanic",
    "pyjwt",
    # 'uvloop',  # XXX setup crashes by not being 'able to create executables'
    "cryptography",
    "codecov",
]

extras_require = {
    "docs": [
        # 'sphinx_rtd_theme',
        "Sphinx"
    ],
    "tests": tests_require,
}

extras_require["all"] = []
for reqs in extras_require.values():
    extras_require["all"].extend(reqs)

setup_requires = ["pytest-runner"]

install_requires = ["pyjwt"]

setup(
    name="sanic-jwt",
    version="1.1.2",
    description="JWT oauth flow for Sanic",
    url="https://github.com/ahopkins/sanic-jwt",
    download_url="https://github.com/ahopkins/sanic-jwt/archive/master.zip",
    author="Adam Hopkins",
    author_email="admhpkns@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    keywords="sanic oauth authentication jwt",
    packages=find_packages(exclude=["example", "tests"]),
    install_requires=install_requires,
    extras_require=extras_require,
    setup_requires=setup_requires,
    tests_require=tests_require,
    package_data={},
)
