Example Analyses
================
This document provides detailed walkthroughs of analysis on real datasets. The datasets are provided in the source code, under `BayesDB/examples`.

Dartmouth Health Atlas Dataset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The Dartmouth Health Atlas dataset is a compilation of information about hospitals, such as quality of care and cost of care.

Getting set up
^^^^^^^^^^^^^^

.. ipython::

   In [1]: from bayesdb.client import Client
   
   In [2]: client = Client()

For demo purposes, we will make sure to delete the old dha btable with the same name, to avoid an error message when we try to create a second btable with that name. Normally DROP BTABLE prompts the user for confirmation before deleting a table, but we can pass yes=True to override that.

.. ipython::

   In [3]: client('DROP BTABLE dha', yes=True)

First, create the btable.

.. ipython::

   In [3]: client('CREATE BTABLE dha FROM ../examples/dha/dha.csv;', key_column=0)

Then, analyze the data::

	INITIALIZE 64 MODELS FOR dha;
	ANALYZE dha FOR 300 ITERATIONS;

Or, if you have already initialized and analyzed models for this dataset in the past, you may load those models in now.

.. ipython::

   In [4]: client('LOAD MODELS ../examples/dha/dha_models.pkl.gz INTO dha;')

Investigating the data
^^^^^^^^^^^^^^^^^^^^^^
    
Now, let's look at some of the data.

.. ipython::

   In [5]: client("SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha LIMIT 10;")

We can see which columns are related.

.. ipython::

   In [6]: client('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM dha SAVE TO images/dha_dep.png;')

Which generates the following image output, if graphics are enabled (and otherwise prints a text-based version).

.. image:: images/dha_dep.png
   :width: 1000px

While the output is a large matrix (#columns x #columns), an insight about the dependency structure in the data immediately jumps out at us: variables related to quality of healthcare are unrelated to variables related to the cost of healthcare!

Now, to zoom in on parts of this matrix, we can just look at the 6 columns most related to the qual_score column (quality of care). We can select those 6 columns with an ESTIMATE COLUMNS statement, save the column list as a variable, and then use that column list in future commands.

.. ipython::

   In [6]: client('ESTIMATE COLUMNS FROM dha ORDER BY DEPENDENCE PROBABILITY WITH qual_score LIMIT 6 AS qs_cols;')   

Now, we will generate a subsection of the pairwise dependence probability matrix above, by only showing the 6x6 submatrix involving the 6 columns we selected above. Since it is small enough, we can view this matrix as textual output instead of as an image.

.. ipython::

   In [6]: client('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM dha FOR qs_cols SAVE TO images/dha_dep_qs_cols.png;')

.. image:: images/dha_dep_qs_cols.png
   :width: 1000px
   

Let's see which columns are most related to pymt_p_md_visit (payment per doctor visit).

.. ipython::

   In [6]: client('ESTIMATE COLUMNS FROM dha ORDER BY DEPENDENCE PROBABILITY WITH pymt_p_md_visit LIMIT 6 AS pm_cols;')

   In [6]: client('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM dha FOR pm_cols;')

Confirming our hypothesis
^^^^^^^^^^^^^^^^^^^^^^^^^

Let's see which hospitals have healthcare quality most similar to Albany, NY.

.. ipython::

   In [6]: client("SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha ORDER BY SIMILARITY TO name='Albany NY' WITH RESPECT TO qual_score LIMIT 10;")

And which hospitals have payments per doctor visit similar to Albany, NY.

.. ipython::
   
   In [6]: client("SELECT name, qual_score, ami_score,  pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha ORDER BY SIMILARITY TO name='Albany NY' WITH RESPECT TO pymt_p_visit_ratio LIMIT 10;")

Looks like hospitals in the rust belt have the highest payments per doctor visit, but healthcare quality isn't correlated with payments per visit! In fact, the best hospitals seem to be pretty well scattered geographically.



