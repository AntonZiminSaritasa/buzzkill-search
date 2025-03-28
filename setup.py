from setuptools import setup, find_packages

setup(
    name="buzzkill-search",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "tkinter",
    ],
    entry_points={
        'console_scripts': [
            'buzzkill-search=buzzkill_search:main',
        ],
    },
    author="Anton Zimin",
    author_email="anton.zimin@saritasa.com",
    description="Fast file search utility with GUI",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://launchpad.net/buzzkill-search",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment :: File Managers",
    ],
    python_requires=">=3.8",
) 