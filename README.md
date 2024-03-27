# findMe Shared Library

This repository contains the source code for the findMe shared library. It is organized as a python package using poetry
and is then installed via pip.

## Project Structure

```yaml
shared
-- findme # The main package
-- authorization # Contains the authorization module to authenticate the findme API
-- tests # local tests
-- pyproject.toml # The poetry configuration file
```

## Installation

Currently, the library is installed via pip directly from this git repository. This is a functionality enabled py pip
directly `pip install pip@git+https://github.com/uzh-ase-fs24/shared@develop'`

## Usage

```python
from findme.authorization import Authorizer

authorizer = Authorizer(...)
...
```