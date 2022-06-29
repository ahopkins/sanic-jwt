import codecs
import re
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))


def open_local(paths, mode="r", encoding="utf8"):
    p = path.join(here, *paths)
    return codecs.open(p, mode, encoding)


with open_local(["sanic_jwt", "__init__.py"], encoding="latin1") as fp:
    try:
        version = re.findall(
            r"^__version__ = \"([0-9\.]+)\"", fp.read(), re.M
        )[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")

with open_local(["README.md"]) as rm:
    long_description = rm.read()

extras_require = {"docs": ["Sphinx", "Jinja2<3.1"]}

extras_require["all"] = []
for reqs in extras_require.values():
    extras_require["all"].extend(reqs)

install_requires = [
    "pyjwt>=2.4.0,<3.0.0",
]

setup(
    name="sanic-jwt",
    version=version,
    description="JWT oauth flow for Sanic",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="sanic oauth authentication jwt",
    packages=find_packages(exclude=["example", "tests"]),
    install_requires=install_requires,
    extras_require=extras_require,
    package_data={},
)
