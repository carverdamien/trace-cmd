import setuptools, os

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("pip3.install.txt", "r") as fh:
    install_requires = [p for p in fh.read().split("\n") if len(p) > 0]

scripts = [
    os.path.join(dirpath, filename)
    for dirpath, dirnames, filenames in os.walk('scripts')
    for filename in filenames
]

setuptools.setup(
    name="TraceDisplay",
    version="0.0.1",
    author="Damien Carver",
    author_email="carverdamien@gmail.com",
    description="A package to manipulate and visualize trace-cmd records as a collection of pandas DataFrame",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/carverdamien/trace-cmd",
    install_requires=install_requires,
    scripts=scripts,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='==3.7.6',
)
