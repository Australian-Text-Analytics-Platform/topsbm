<a href="https://atap.edu.au"><img src="https://www.atap.edu.au/atap-logo.png" width="125" height="50" align="right"></a>

# ATAP: TopSBM

TopSBM is a topic modelling approach that infers a hierarchy of topic clusters and word clusters in your Corpus
in a non-parametric manner by leveraging stochastic block models. Top (Topic), SBM (Stochastic Block Models). 

This approach was developed in

M. Gerlach, T. P. Peixoto, and E. G. Altmann, "A network approach to topic models", [Sci. Adv. 4, eaaq1360 (2018)](http://doi.org/10.1126/sciadv.aaq1360)

This repository is an integration effort of TopSBM to the ATAP platform.

## Demo

This is demo jupyter notebook for TopSBM with ATAP Corpus integration. At the end of the notebook, you'll be able to
download
a Corpus with TopSBM results. You may then choose to upload this Corpus across to other ATAP tools for further analysis.

[![Binder](https://binderhub.rc.nectar.org.au/badge_logo.svg)](https://binderhub.rc.nectar.org.au/v2/gh/Australian-Text-Analytics-Platform/topsbm/main?labpath=workshop.ipynb)

<b>Note:</b> Australian Access Federation (AAF) or Reannz Tuakiri (NZ) authentication is required.
If you do not have access to AAF or NZ, you can use the below link to access the tool (this is a free Binder version, limited to 2GB memory only).

Demo notebook:
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Australian-Text-Analytics-Platform/topsbm/main?labpath=workshop.ipynb)

# Citations

+ TopSBM website: https://topsbm.github.io/
+ TopSBM repository: https://github.com/martingerlach/hSBM_Topicmodel

## Local
If you are running this repository locally, you'll first need to:
```shell
# 1. activate your virtual environment
./scripts/install_topsbm.sh topsbm
```
