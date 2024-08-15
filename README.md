[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![codecov](https://codecov.io/gh/mscheltienne/template-python/branch/main/graph/badge.svg?token=KRYRRUXDYY)](https://codecov.io/gh/mscheltienne/template-python)
[![tests](https://github.com/mscheltienne/template-python/actions/workflows/pytest.yaml/badge.svg?branch=main)](https://github.com/mscheltienne/template-python/actions/workflows/pytest.yaml)
[![doc](https://github.com/mscheltienne/template-python/actions/workflows/doc.yaml/badge.svg?branch=main)](https://github.com/mscheltienne/template-python/actions/workflows/doc.yaml)

# template-python

## Package

Template python repository. To bootstrap a project from this template, the
following steps are required:

- [x] Rename the folder `template` to the package name
- [x] Edit `pyproject.toml`
    - [x] Under `[project]`, edit `name`, `description` and `keywords`
    - [x] Under `[project.optional-dependencies]`, edit the extra-keys `all` and `full`
    - [x] Under `[project.urls]`, edit all the URLs
    - [x] Under `[project.scripts]`, edit the command for system information
    - [x] Under `[tool.setuptools.packages.find]`, edit the file inclusion/exclusion patterns
    - [x] Under `[tool.pydocstyle]`, edit the matching pattern `match-dir`
    - [x] Under `[tool.coverage.run]`, edit the exclusion patterns `omit`
- [x] Edit the GitHub workflows
    - [x] In `doc.yaml`, edit the command for system information
    - [x] In `publish.yaml`, uncomment the trigger on release and edit the command for system information
    - [x] In `pytest.yaml`, edit the commands for system information and pytest
- [x] Edit the pre-commit configuration
    - [x] Edit the paths in `.pre-commit-config.yaml`
    - [x] Enable `pre-commit.ci` on https://pre-commit.ci/
- [ ] Edit `README.md`
- [x] Edit `MANIFEST.in`
- [ ] Edit the keys to list in the system information
- [ ] Remove the conda-forge recipe from the ignored files in ``.yamllint.yaml``

The package can then be installed in a given environment with
`pip install -e .` (assuming the current working directory is the root of the
repository).

## Documentation build

If the documentation build is preserved, the following steps are required:

On the `main` branch:
- [x] Edit the GitHub workflows
    - [x] In `doc.yaml`, edit the command for system information
- [x] Edit the project links in `doc\links.inc`
- [x] Edit the landing page `index.rst`
- [x] Edit the sphinx configuration
    - [x] Replace `import template` with the correct package name
    - [x] Edit the fields `project`, `author`, `release`, `package` and `gh_url`
- [x] Edit the API pages
    - [x] In `doc\api\index.rst`, edit the package name
    - [x] In `doc\api\logging.rst`, edit the current module
- [x] Edit the logging tutorial to replace `from template import` with the correct package name

On the `gh-pages` branch:
- [ ] Edit the links in the landing page `index.html`
