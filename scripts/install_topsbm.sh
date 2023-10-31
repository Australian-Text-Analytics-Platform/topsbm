#!/bin/zsh
# This script installs topsbm into your local conda virtual environment.
# make sure you have activated your conda environment.

HELP="./$(basename $0) <user-defined topsbm package name>"

if [[ -z $1 ]]; then
    echo $HELP;
    exit 1
fi
PKG_NAME=$1

SITEPACKAGES_DIR=$(python <<EOF
import site
spkgs = site.getsitepackages()
if len(spkgs) == 1:
  print(spkgs[0])
else:
  raise RuntimeError("Expecting one site-packages path only")
EOF
)
PKG_PATH="${SITEPACKAGES_DIR}/${PKG_NAME}"
echo "PYTHON=$(which python)"
echo "SITEPACKAGES=$SITEPACKAGES_DIR"
echo "INSTALL_TO=$PKG_PATH"

printf "Confirm? (y/n): " && read x && [[ $x == 'y' ]] || exit 1

echo "Cloning to $PKG_PATH..."
git clone --quiet https://github.com/martingerlach/hSBM_Topicmodel.git $PKG_PATH
echo "Done. Cloned to $PKG_PATH"
echo "You may now import ${PKG_NAME}."