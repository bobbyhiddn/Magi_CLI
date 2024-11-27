from setuptools import setup, find_packages

# Read the contents of your README file
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='magi_cli_pypi',
    version='1.0.1',  # Make sure to increment this if you are republishing
    packages=find_packages(),
    package_data={'magi_cli': ['artifacts/*.png']},
    include_package_data=True,
    install_requires=[
        'Click',
        'requests',
        'setuptools'
    ],
    entry_points={
        'console_scripts': [
            'cast=magi_cli.cast:cast',
        ],
    },
    author="Micah Longmire",
    author_email="mlmicahlongmire@gmail.com",
    description="Magi_CLI is a command line interface for those who desire software development to feel more like magic.",
    long_description=long_description,
    long_description_content_type='text/markdown',  # Ensure this is correct
    url="https://github.com/bobbyhiddn/Magi_CLI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
