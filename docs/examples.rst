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

   In [3]: client('CREATE BTABLE dha FROM ../examples/dha/dha.csv;')

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

   In [6]: client('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM dha FOR COLUMNS qs_cols SAVE TO images/dha_dep_qs_cols.png;')

.. image:: images/dha_dep_qs_cols.png
   :width: 1000px
   

Let's see which columns are most related to pymt_p_md_visit (payment per doctor visit).

.. ipython::

   In [6]: client('ESTIMATE COLUMNS FROM dha ORDER BY DEPENDENCE PROBABILITY WITH pymt_p_md_visit LIMIT 6 AS pm_cols;')

   In [6]: client('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM dha FOR COLUMNS pm_cols;')

Confirming our hypothesis
^^^^^^^^^^^^^^^^^^^^^^^^^

Let's see which hospitals have healthcare quality most similar to Albany, NY.

.. ipython::

   In [6]: client("SELECT name, qual_score, ami_score, pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha ORDER BY SIMILARITY TO name='Albany NY' WITH RESPECT TO qual_score LIMIT 10;")

And which hospitals have payments per doctor visit similar to Albany, NY.

.. ipython::
   
   In [6]: client("SELECT name, qual_score, ami_score,  pymt_p_visit_ratio, ttl_mdcr_spnd, hosp_reimb_ratio, hosp_reimb_p_dcd, md_copay_p_dcd, ttl_copay_p_dcd FROM dha ORDER BY SIMILARITY TO name='Albany NY' WITH RESPECT TO pymt_p_visit_ratio LIMIT 10;")

Looks like hospitals in the rust belt have the highest payments per doctor visit, but healthcare quality isn't correlated with payments per visit! In fact, the best hospitals seem to be pretty well scattered geographically.



2012 General Social Survey
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The General Social Survey is a comprehensive survey about a wide variety of topics given to a sample of U.S. Citizens. In this example, we'll analyze a subset of the data that includes 100 columns (survey questions) and 1973 rows (people).

Getting set up
^^^^^^^^^^^^^^

.. ipython::

   In [1]: from bayesdb.client import Client
   
   In [2]: client = Client()

For demo purposes, we will make sure to delete the old gss btable with the same name, to avoid an error message when we try to create a second btable with that name. Normally DROP BTABLE prompts the user for confirmation before deleting a table, but we can pass yes=True to override that.

.. ipython::

   In [3]: client('DROP BTABLE gss', yes=True)

Now, create the btable.

.. ipython::

   In [3]: client('CREATE BTABLE gss FROM ../examples/gss/gss.csv;')

Then, analyze the data::

	INITIALIZE 64 MODELS FOR gss;
	ANALYZE gss FOR 300 ITERATIONS;

Or, if you have already initialized and analyzed models for this dataset in the past, you may load those models in now.

.. ipython::

   In [4]: client('LOAD MODELS ../examples/gss/gss_models.pkl INTO gss;')

Analyzing the data
^^^^^^^^^^^^^^^^^^
The jist of this analysis is to illustrate how we might explore a dataset with many columns.

First, get the full dependence probability matrix.

.. ipython::
  
   In [5]: client('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM gss SAVE TO images/gss_dep.png;')

Which generates the following image output, if graphics are enabled (and otherwise prints a text-based version).

.. image:: images/gss_dep.png
   :width: 1000px

That's a lot of variables! You can imagine that any dataset with more than 100 columns would require limiting the number of columns we're examining simultaneously, but we will do it here anyway because it will still help us focus.

.. ipython::

   # Pick out the 10 columns most dependent with racecen1
   In [6]: client('ESTIMATE COLUMNS FROM gss ORDER BY DEPENDENCE PROBABILITY WITH racecen1 LIMIT 10 AS racecen1_cols;')

   # Generate the pairwise dependence probability matrix with that column subset.
   In [7]: client('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM gss FOR COLUMNS racecen1_cols SAVE TO images/gss_dep_race1.png')

.. image:: images/gss_dep_race1.png
   :width: 1000px

Now, let's examine the 10 most typical columns:

.. ipython::

   # Pick out the 10 most typical columns.
   In [6]: client('ESTIMATE COLUMNS FROM gss ORDER BY TYPICALITY DESC LIMIT 10 AS typical10col;')

   # Generate the pairwise dependence probability matrix with that column subset.
   In [7]: client('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM gss FOR COLUMNS typical10col SAVE TO images/gss_dep_typ10.png;')

.. image:: images/gss_dep_typ10.png
   :width: 1000px

Inspect this submatrix to see how many of the clusters from the large matrix are represented:

-- seeksci (where do you seek info re: science) is in the middle of the matrix in a small cluster of two with sprel (spouse religious affliation). can see that it is associated with most variables.

-- kidjoy (watching kids grow up is greatest joy) is further down in the same large grouping with scientdn (scientific work is dangerous). less dependent.

-- polefy16 (elected people try to keep promises) is third from the bottom with intlblks (are blacks intelligent), engnrsci (is engineering scientific).

-- racecen1 (respondents race) is in the large middle grouping with whoelse2 (were children >6 present)

-- scientod (scientists are odd) is second from the bottom of the large middle grouping

.. ipython::

   # -- Look at this subset to get a sense of how they are related
   In [8]: client('SELECT typical10col FROM gss LIMIT 20;')



.. ipython::

   # -- Lots of missing values, maybe fill in to better see relationships
   #In [9]: client('INFER typical10col from gss WITH CONFIDENCE .9 LIMIT 20;')


-- Note that the values were not filled in. Why? To simultaneously estimate many variables takes considerably more information than one or two variables, and we don't have enough at the moment. If we focus on just pairs, we will have better luck

-- Focus on religion for differences

.. ipython::
   
   #In[10]: client('SIMULATE typical10col FROM gss WHERE sprel=1 times 50;')
   
   #In[11]: client('SIMULATE typical10col FROM gss WHERE sprel=2 times 50;')
   
   #In[12]: client('SIMULATE typical10col FROM gss WHERE sprel=3 times 50;')
   
-- Not huge differences. Minor things like where science info comes from (Protestants go to internet or govt, Catholics are a bit more variable, Jewish folks are more likely to look to books)

-- Note proportions of races: http://religions.pewforum.org/ reports that 81% of protestants are white, 65% of catholics, and 95%

-- Proportions are closely matched to simulation results, providing a nice cross-validation of the model.

-- Try race: 1) white, 2) black, 4) asian, 16) hispanic

.. ipython::
   
   #In[13]: client('SIMULATE typical10col FROM gss WHERE racecen1=1 times 50;')
   
   #In[14]: client('SIMULATE typical10col FROM gss WHERE racecen1=2 times 50;')
   
   #In[15]: client('SIMULATE typical10col FROM gss WHERE racecen1=16 times 50;')

