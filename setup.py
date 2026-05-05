from setuptools import setup, find_packages

setup(
    name="claude-cognition",
    version="1.0.0",
    author="bes1705",
    author_email="stadelmann.sebastien1@gmail.com",
    description="Persistent 3-layer cognitive memory for Claude Code — decisions, patterns, and the WHY that survives every session",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/bes1705/claude-cognition",
    packages=find_packages(),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "cognition=cognition.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="claude claude-code ai-memory llm-memory persistent-memory cognitive-graph anthropic",
)
