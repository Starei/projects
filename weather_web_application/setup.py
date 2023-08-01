from pathlib import Path

from setuptools import find_namespace_packages, setup

# Load packages from requirements.txt
BASE_DIR = Path(__file__).parent
with open(Path(BASE_DIR, "requirements.txt"), "r") as file:
    required_packages = [package.strip() for package in file.readlines()]

style_packages = ["black==23.3.0", "flake8==6.0.0", "isort==5.12.0"]

test_packages = [
    "pytest==7.4.0",
    "pytest-cov==4.1.0",
    "great-expectations==0.17.4",
]

# Define our package
setup(
    name="app_package",
    version=0.1,
    description="Daily temperature and precipitation probability prediction",
    author="Dima Brishten",
    author_email="dima.brishten@mail.ru",
    python_requires=">=3.7",
    packages=find_namespace_packages(),
    install_requires=[required_packages],
    extras_require={
        "dev": style_packages + test_packages,
        "test": test_packages,
    },
)

# To install the package, write: pip install .
# To install all needed packages, use: pip install -r requirements.txt
