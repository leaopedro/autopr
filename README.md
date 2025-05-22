# AutoPR

A CLI tool for creating PRs using AI.

## Installation

You can install AutoPR using pip:

```sh
pip install autopr_cli
```

## Usage
To create a new PR:
```sh
autopr create --title "PR Title"
```


## To publish a new version:

After changes are done, run the following:

1: Build the package:
```sh
python setup.py sdist bdist_wheel
```

2: upload:

```sh
twine upload dist/*
```