import setuptools

ver_globals = {}
with open("herbie/version.py") as fp:
    exec(fp.read(), ver_globals)
version = ver_globals["version"]

setuptools.setup(
    name="herbie",
    version=version,
    author="Brett Viren",
    author_email="brett.viren@gmail.com",
    description="Herbstluftwm Interactive Environment",
    url="https://brettviren.github.io/herbie",
    packages=setuptools.find_packages(),
    python_requires='>=3.5',
    install_requires=[
        "click",
        "sexpdata",
        "anytree",
        "rofi_menu",
        ## these are needed in venv, but fail for user install
        ## if needed, install them manually.
        # "vext",
        # "vext.gi",
    ],
    entry_points = dict(
        console_scripts = [
            'herbie = herbie.__main__:main',
        ]
    ),
    include_package_data=True,
)

