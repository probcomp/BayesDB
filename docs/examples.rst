Example Analyses
================
This document provides detailed walkthroughs of analysis on real datasets. The datasets are provided in the source code, under `bayesdb/tests/data`.

Dartmouth Health Atlas Dataset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The Dartmouth Health Atlas dataset is a compilation of information about hospitals, such as quality of care and cost of care.

Getting set up
^^^^^^^^^^^^^^

First, create the btable::

        CREATE BTABLE dha FROM tests/data/dha.csv

Then, analyze the data::

	CREATE 20 MODELS FOR dha
	ANALYZE dha FOR 500 ITERATIONS

Or, if you want to proceed to the next step immediately, you can import already-generated samples::

    IMPORT SAMPLES samples/dha_samples.pkl.gz INTO dha

Investigating the data
^^^^^^^^^^^^^^^^^^^^^^
    
Now, let's look at some of the data::

     SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio,
            hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd
     FROM dha_demo LIMIT 10

We can see which columns are related::

   ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo

There's a lot of uncessary information in the full column matrix, so let's just look at the 6 columns most related to the qual_score column (quality of care)::

   ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING qual_score LIMIT 6

Adding a confidence threshold of 0.9 to this query doesn't change the results, because we were already very confident::

       ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING qual_score WITH CONFIDENCE 0.9

Let's see which columns are most related to pymt_p_md_visit (payment per doctor visit)::

      ESTIMATE DEPENDENCE PROBABILITIES FROM dha_demo REFERENCING pymt_p_md_visit LIMIT 6

Confirming our hypothesis
^^^^^^^^^^^^^^^^^^^^^^^^^

Let's see which hospitals have healthcare quality most similar to Albany, NY::

	SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio,
	       hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd
	FROM dha_demo
	ORDER BY similarity_to(name='Albany NY', qual_score), ami_score
	LIMIT 10

And which hospitals have payments per doctor visit similar to Albany, NY::
	
        SELECT name, qual_score, ami_score,  pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio,
	       hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd
	FROM dha_demo
	ORDER BY similarity_to(name='Albany NY', pymt_p_visit_ratio), ttl_mdcr_spnd
	LIMIT 10

Looks like hospitals in the rust belt have the highest payments per doctor visit, but healthcare quality isn't correlated with payments per visit! In fact, the best hospitals seem to be pretty well scattered geographically.
