from setuptools import find_packages, setup

setup(
    name="angis",
    version="0.1.0",
    packages=find_packages(include=["angis", "angis.*"]),
    entry_points={
        "console_scripts": [
            "angis=angis.cli:main",
        ],
    },
    python_requires=">=3.11",
)
