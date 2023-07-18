from setuptools import setup, find_packages

setup(
    name="magi_cli",
    version="0.1.0",
    packages=find_packages(),  # Automatically find all packages
    package_data={
        'artifacts': ['*.png'],  # Include all .png files in the spells/ directory
    },
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
