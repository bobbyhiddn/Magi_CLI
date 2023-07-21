from setuptools import setup, find_packages

setup(
    name='magi_cli',
    version='0.1.1',
    packages=find_packages(),
    package_data={'magi_cli': ['artifacts/*.png']},
    include_package_data=True,
    install_requires=[
        'Click',
        'openai',
        'requests',
        'Pillow',
        'python-dotenv',
        'gitpython',
        'flask',
        'PyQt5',
    ],
    entry_points='''
        [console_scripts]
        cast=magi_cli.cast:cast
    ''',
    author="Micah Longmire",
    author_email="mlmicahlongmire@gmail.com",
    description="Magi_CLI is a command line interface for those who desire software development to feel more like magic.",
    url="https://github.com/bobbyhiddn/Magi_CLI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
