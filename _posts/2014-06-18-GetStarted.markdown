---
layout: default
title: Download
tagline: Download. Install. Explore.
---

BayesDB is currently available via [Github](https://github.com/mit-probabilistic-computing-project/BayesDB).

In addition, BayesDB can also be accessed via a community-contributed [Docker](http://www.docker.com/) container, currently built weekly. Install instructions for Docker can be found [here](https://docs.docker.com/installation/#installation). <!-- **Note:** Though Docker is compatible with many platforms, the container is tested only on Mac OSX, Ubuntu, and Microsoft Windows. -->

Once docker has been installed and configured enter the following command in your Unix/Linux terminal to download and install the Docker container (this will take a few minutes):

	docker pull bayesdb/bayesdb

Start docker and load the Dartmouth Atlas of Health example:

	$ docker run -i -t bayesdb/bayesdb /bin/bash
	$ cd examples/dha
    $ bql
    bql> create btable dha from dha.csv
    +--------+---------------------+
    | choice |      key column     |
    +--------+---------------------+
    |   0    | <Create key column> |
    |   1    |         name        |
    |   2    |    ttl_mdcr_spnd    |
    +--------+---------------------+
    Please select which column you would like to set as the table key:
    1
    bql> load models dha_models.pkl.gz into dha
    +----------+------------+
    | model_id | iterations |
    +----------+------------+
    |    0     |    500     |
    |    1     |    500     |
    |    2     |    500     |
    |    3     |    500     |
    |    4     |    500     |
    |    5     |    500     |
    |    6     |    500     |
    |    7     |    500     |
    |    8     |    500     |
    |    9     |    500     |
    +----------+------------+

List variables by their dependence probability with the quality score (`qual_score`):

    bql> ESTIMATE COLUMNS FROM dha ORDER BY DEPENDENCE PROBABILITY WITH qual_score LIMIT 10
    +------------------+----------------------------------------+
    |      column      | dependence probability with qual_score |
    +------------------+----------------------------------------+
    |    qual_score    |                  1.0                   |
    | mdcr_spnd_other  |                  1.0                   |
    |  pct_dths_hosp   |                  0.8                   |
    |  mdcr_spnd_hspc  |                  0.7                   |
    |  mdcr_spnd_eqp   |                  0.5                   |
    |   partb_other    |                  0.4                   |
    | partb_eval_mgmt  |                  0.4                   |
    |  md_copay_p_dcd  |                  0.4                   |
    |   partb_tests    |                  0.4                   |
    | hosp_reimb_p_dcd |                  0.4                   |
    +------------------+----------------------------------------+

For more examples see the [examples page]({{ site.baseurl }}{% post_url 2014-07-16-examples%}).

<!-- Users with Linux shell and python experience who wish to perform a custom install of the source are directed to [the code repository](https://github.com/mit-probabilistic-computing-project/BayesDB). -->
