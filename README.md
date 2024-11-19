<a href="https://atap.edu.au"><img src="https://www.atap.edu.au/atap-logo.png" width="125" height="50" align="right"></a>

# ATAP: TopSBM

TopSBM is a topic modelling approach that infers a hierarchy of topic clusters and word clusters in your Corpus
in a non-parametric manner by leveraging stochastic block models.

The approach is developed by E.G. Altman et al.

Top (Topic), SBM (Stochastic Block Models).

This repository is an integration effort of TopSBM to the ATAP platform.

## Demo

This is demo jupyter notebook for TopSBM with ATAP Corpus integration. At the end of the notebook, you'll be able to
download
a Corpus with TopSBM results. You may then choose to upload this Corpus across to other ATAP tools for further analysis.

[//]: # (Demo notebook &#40;minimal&#41;:)
[//]: # ([![Binder]&#40;https://binderhub.atap-binder.cloud.edu.au/badge_logo.svg&#41;]&#40;https://binderhub.atap-binder.cloud.edu.au/v2/gh/Australian-Text-Analytics-Platform/topsbm.git/16aa44933f73f59ee6e301739cd12d814a1cd9a6?labpath=workshop.ipynb&#41;)

Demo notebook:
[![Binder](https://binderhub.atap-binder.cloud.edu.au/badge_logo.svg)](https://binderhub.atap-binder.cloud.edu.au/v2/gh/Australian-Text-Analytics-Platform/topsbm.git/585c8425cb50047de1adfda2acbacc65df1f3692?labpath=workshop.ipynb)

# Citations

+ TopSBM website: https://topsbm.github.io/
+ TopSBM repository: https://github.com/martingerlach/hSBM_Topicmodel

## Local
If you are running this repository locally, you'll first need to:
```shell
# 1. activate your virtual environment
./scripts/install_topsbm.sh topsbm
```
