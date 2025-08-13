from setuptools import find_packages, setup

setup(
    name="audio-analyzer",
    version="1.0.0",
    description="Async audio analysis and classification API",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "httpx>=0.25.2",
        "aiofiles>=23.2.1",
        "librosa>=0.10.1",
        "pydub>=0.25.1",
        "soundfile>=0.12.1",
        "numpy>=1.24.4",
        "redis[hiredis]>=5.0.1",
        "loguru>=0.7.2",
        "prometheus-client>=0.19.0",
        "prometheus-fastapi-instrumentator>=6.1.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
        ]
    },
)
