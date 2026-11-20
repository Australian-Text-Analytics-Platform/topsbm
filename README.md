<a href="https://atap.edu.au"><img src="https://www.atap.edu.au/atap-logo.png" width="125" height="50" align="right"></a>

# ATAP: TopSBM

> [!WARNING]
> **This tool is archived and no longer supported or maintained.**
> It was developed by the Australian Text Analytics Platform (ATAP), the previous phase of the
> Language Data Commons of Australia (LDaCA). It is preserved as a frozen Docker image so that it
> keeps launching on BinderHub as it last worked, but it will not be updated or fixed.
> For current LDaCA text analytics tools, please use
> [Wordflow](https://australian-text-analytics-platform.github.io/LDaCa_Text_Analytics_Tools/) and
> [LADAL](https://ladal.edu.au).

TopSBM is a topic modelling approach that infers a hierarchy of topic clusters and word clusters in your Corpus
in a non-parametric manner by leveraging stochastic block models.

The approach is developed by E.G. Altman et al.

Top (Topic), SBM (Stochastic Block Models).

This repository is an integration effort of TopSBM to the ATAP platform.

## Demo

This is demo jupyter notebook for TopSBM with ATAP Corpus integration. At the end of the notebook, you'll be able to
download
a Corpus with TopSBM results. You may then choose to upload this Corpus across to other ATAP tools for further analysis.

[![Binder](https://binderhub.rc.nectar.org.au/badge_logo.svg)](https://binderhub.rc.nectar.org.au/v2/gh/Australian-Text-Analytics-Platform/topsbm/archived?labpath=workshop.ipynb)

<b>Note:</b> Australian Access Federation (AAF) or Reannz Tuakiri (NZ) authentication is required.
If you do not have access to AAF or NZ, you can use the below link to access the tool (this is a free Binder version, limited to 2GB memory only).

Demo notebook:
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Australian-Text-Analytics-Platform/topsbm/archived?labpath=workshop.ipynb)

# Citations

+ TopSBM website: https://topsbm.github.io/
+ TopSBM repository: https://github.com/martingerlach/hSBM_Topicmodel

## Local
If you are running this repository locally, you'll first need to:
```shell
# 1. activate your virtual environment
./scripts/install_topsbm.sh topsbm
```

## Run locally with Docker

The frozen environment of this tool is published as the Docker image
[`milysun/atap-topsbm`](https://hub.docker.com/r/milysun/atap-topsbm). With [Docker](https://docs.docker.com/get-docker/) installed, run:

```bash
docker run --rm -p 8888:8888 milysun/atap-topsbm:1eb3468786ac jupyter lab --ip=0.0.0.0 --port=8888
```

then open the `http://127.0.0.1:8888/lab?token=...` link printed in the terminal.
On Apple Silicon Macs add `--platform linux/amd64` after `docker run`.
