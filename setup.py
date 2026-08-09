from setuptools import setup, find_packages

setup(
    name="mermicorn-commerce-ai",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=7.0", "ruff>=0.1.0"],
    },
)
