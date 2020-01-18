import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flask-download-btn",
    version="0.0.17",
    author="Dillon Bowen",
    author_email="dsbowen@wharton.upenn.edu",
    description="Flask-Download-Btn defines a SQLALchemy Mixin for creating Bootstrap download buttons in a Flask application.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dsbowen/flask-download-btn",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'flask==1.1.1',
        'sqlalchemy==1.3.12',
        'sqlalchemy_function==0.0.5',
        'sqlalchemy_modelid==0.0.2',
        'sqlalchemy_mutable==0.0.7',
        'sqlalchemy_mutablesoup==0.0.5',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)