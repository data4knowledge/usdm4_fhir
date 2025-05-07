import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

package_info = {}
with open("src/usdm4_excel/__version__.py") as fp:
    exec(fp.read(), package_info)

setuptools.setup(
    name="usdm4_excel",
    version=package_info["__package_version__"],
    author="D Iberson-Hurst",
    author_email="",
    description="A python package for importing and exporting the CDISC TransCelerate USDM, version 4, using Excel",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["usdm4", "openpyxl"],
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    package_data={},
    tests_require=["pytest", "pytest-cov", "pytest-mock", "python-dotenv"],
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)
