import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flask-download-btn",
    version="0.0.14",
    author="Dillon Bowen",
    author_email="dsbowen@wharton.upenn.edu",
    description="Flask-Download-Btn defines a SQLALchemy Mixin for creating Bootstrap download buttons in a Flask application.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dsbowen/flask-download-btn",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)