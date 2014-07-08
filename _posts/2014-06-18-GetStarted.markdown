---
layout: default
title: Get Started
tagline: Download. Install. Explore.
---
	
BayesDB is distributed via a [Docker](http://www.docker.com/) container which is built weekly. Install intructions for Docker can be found [here](https://docs.docker.com/installation/#installation). **Note: Though Docker is compatible with many platforms, the container is only tested on Mac OSX and Ubuntu 12.04.**

Once docker has been installed and configured enter the following command in your Unix/Linux terminal to download and install the Docker container (this will take a few minutes):

	docker pull avinson/bayesdb

To run the Dartmouth Atlas of Health example analysis:

	docker run -i -t avinson/bayesdb /bin/bash
	su - bayesdb
	cd BayesDB/ && python examples/dha/run_dha_example.py

Users with Linux shell and python experience who wish to perform a custom install of the source are directed to [the code repository](https://github.com/mit-probabilistic-computing-project/BayesDB).
