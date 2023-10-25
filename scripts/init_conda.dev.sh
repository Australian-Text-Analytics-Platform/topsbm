#!/bin/zsh
# This script initialises a python virtual environment.
# It expects you to have Python installed at the system-level uses it for the virtual env.
# It also checks whether your system's OS and Architecture to install the appropriate dependant extras.
# All other extras and groups are installed (e.g. viz, dev)
# For any issues:
# + try to run this script from the project root level.

set -e

HELP="./$(basename $0) <conda-virutal-env-name>"


if [[ -z $1 ]]; then
  echo "-- $HELP" >&2
  exit 1
fi

VENV_NAME=$1
CONDA_ENV_FILE=$(realpath "environment.yml")
OS=$(uname -o)
ARCH=$(uname -m)

echo "CONDA_ENV=$CONDA_ENV_FILE"
echo "OS=$OS"
echo "ARCH=$ARCH"
echo "CONDA=$CONDA_EXE version=$(conda --version)"
echo "PYTHON=$CONDA_PYTHON_EXE version=$($CONDA_PYTHON_EXE --version | awk '{print $2}')"
printf "Confirm? (y/n) "
read x && [[ $x != 'y' ]] && { echo "Exited"; exit 0 }

if [[ ! -f $CONDA_ENV_FILE ]]; then
  echo "-- Missing $CONDA_ENV_FILE." >&2
  exit 1
fi

if [[ ! -z $(conda env list | grep -E "^$VENV_NAME") ]]; then
  printf "-- $VENV_NAME already exist. Remove? (y/n): "
  read x && [[ $x != 'y' ]] && { echo "Exited"; exit 0 }
  conda env remove -n $VENV_NAME
fi

echo "++ Creating conda virtual env at $VENV_NAME..."
conda env create --file $CONDA_ENV_FILE

echo "++ Done. Your conda virtual env is installed at $VENV_NAME"
echo "To activate your virtual env run: conda activate $VENV_NAME"
exit 0