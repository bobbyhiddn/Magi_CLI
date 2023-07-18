from setuptools import setup, find_packages
from setuptools import setup, find_packages

setup(
    name="magi_cli",
    version="0.1.0",
    packages=find_packages(),  # Automatically find all packages
    install_requires=[
        "Click",
        "openai",
        "requests",
        "Pillow",
        "python-dotenv",
        "gitpython",
        "flask"
    ],
    entry_points={
        'console_scripts': [
            'cast = magi_cli.cast:cast'
        ],
    },
)
