#!/usr/bin/env python3
"""
Setup script for DeepCode - Free AI Coding Assistant
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    requirements = [line.strip() for line in requirements_file.read_text().splitlines() 
                   if line.strip() and not line.startswith('#')]
else:
    requirements = [
        'click>=8.0.0',
        'requests>=2.28.0',
        'pyyaml>=6.0',
        'rich>=13.0.0',
        'gitpython>=3.1.0',
        'watchdog>=3.0.0',
        'pygments>=2.14.0'
    ]

setup(
    name="deepcode-ai",
    version="1.1.0",
    description="Free AI coding assistant powered by DeepSeek V2 Coder through Ollama",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DeepCode Team",
    author_email="team@deepcode.dev",
    url="https://github.com/deepcode-ai/deepcode",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=["main", "terminal_ui"],
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'isort>=5.12.0',
            'mypy>=1.0.0',
            'pre-commit>=3.0.0',
        ],
        'docs': [
            'sphinx>=5.0.0',
            'sphinx-rtd-theme>=1.0.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'deepcode=main:cli',
            'dpcd=terminal_ui:main',
            'conflict-deepcode=main:cli',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    keywords="ai coding assistant deepseek ollama code generation programming",
    python_requires=">=3.8",
    project_urls={
        "Bug Reports": "https://github.com/deepcode-ai/deepcode/issues",
        "Source": "https://github.com/deepcode-ai/deepcode",
        "Documentation": "https://deepcode-ai.readthedocs.io/",
    },
)