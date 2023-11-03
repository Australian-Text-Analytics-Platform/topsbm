#!/bin/zsh
# this script exports CURRENT conda env to environment.yml
# note: a new environment will not be created as it depends on the environment.yml file.

EXPORT_TO="environment.yml"

echo "PYTHON=$(which python) version=$(python --version)"
echo "CONDA=$CONDA_EXE version=$(conda --version)"
echo "EXPORT_TO=$EXPORT_TO"

echo "++ Please check above for correct environment to export from."
printf "Confirm? (y/n): " && read x && [[ $x == 'y' ]] || exit 0

if [[ -f $EXPORT_TO ]]; then
  printf "-- $EXPORT_TO exists. Replace? (y/n): " && read x && [[ $x == 'y' ]] || exit 0
fi

# unwanted 'PREFIX' when using conda env export - removed with tail chain
conda env export | tail -r | tail -n +2 | tail -r | grep -v 'jupyter' > $EXPORT_TO

echo "++ Done. Exported to $EXPORT_TO"