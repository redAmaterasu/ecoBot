"""
Setup script for HeshmatBot - Telegram Bot
"""

from setuptools import setup, find_packages
import os

# خواندن محتوای README
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "ربات تلگرام HeshmatBot"

# خواندن requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "pyTelegramBotAPI==4.14.0",
            "python-dotenv==1.0.0",
            "mysql-connector-python==8.2.0"
        ]

setup(
    name="heshmatbot",
    version="1.0.0",
    author="HeshmatBot Developer",
    author_email="developer@heshmatbot.com",
    description="یک ربات تلگرام ساده و کاربردی با Python و MySQL",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/heshmatbot",
    py_modules=["bot", "database"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=3.0",
            "sphinx-rtd-theme>=0.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "heshmatbot=bot:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="telegram bot python telebot mysql database",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/heshmatbot/issues",
        "Source": "https://github.com/yourusername/heshmatbot",
        "Documentation": "https://heshmatbot.readthedocs.io/",
    },
)
