from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="silentreach",
    version="1.0.0",
    author="y Kycportal",
    description="Web intelligence framework combining agent-reach + nodriver for social media scraping with extra skillsets for excellent results. Published in different formats.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ykycportal/silentreach",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "agent-reach @ git+https://github.com/Panniantong/agent-reach.git@v1.5.0",
        "nodriver>=0.38",
        "beautifulsoup4>=4.12",
        "httpx>=0.27",
        "aiohttp>=3.9",
        "yt-dlp>=2024.0",
        "pyyaml>=6.0",
        "rich>=13.0",
        "python-dotenv>=1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-asyncio>=0.23",
            "black>=24.0",
            "ruff>=0.4",
        ],
        "kg": [
            "semantica>=0.7.0",
            "neo4j>=5.0.0",
        ],
        "redis": [
            "redis>=5.0",
        ],
        "proxy": [
            "requests[socks]>=2.31",
        ],
        "export": [
            "reportlab>=4.0",
            "openpyxl>=3.1",
            "odfpy>=1.4",
        ],
        "all": [
            "reportlab>=4.0",
            "openpyxl>=3.1",
            "odfpy>=1.4",
            "gspread>=6.0",
            "google-auth>=2.0",
            "redis>=5.0",
            "requests[socks]>=2.31",
            "semantica>=0.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "silentreach=scripts.silentreach:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
