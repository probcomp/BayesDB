Getting Started
===============
This document is a quick tutorial to get you started loading your own data into BayesDB and running a few queries on it.

See the :doc:`bql` for more detailed information on BQL queries, or check out :doc:`examples` for in-depth sample data analyses that were done using BayesDB.


Create a Client
~~~~~~~~~~~~~~~

In Python (either at a prompt, or in your own module), create a Client::

     from bayesdb.client import Client
     client = Client()

The client defaults to looking for a local BayesDB Engine, which is the most common setup. However, if you want to connect to a remote BayesDB Engine, just pass the hostname and port (default 8008) to the Client's constructor::

    client = Client(hostname='bayesdbserver.com', port=1234)

Once your client is created, you may pass it BQL commands to execute::

     client.execute('SELECT * FROM table;')

Or, for short::

    client('SELECT * FROM table;')


Import your Dataset
~~~~~~~~~~~~~~~~~~~

To import your dataset, first convert it to CSV (comma separated values) format. Unfortunately, no other file formats are supported yet. The first row must consist of comma separated column names, and subsequent lines must each consist of comma separated values; each row must have the same number of commas. Here's an example::

   name, age, grade
   Joe, 12, 7
   Sally, 14, 9
   Jill, 12, 8

Missing values my be indicated by simply omitting the value, or using 'nan', 'null', or 'n/a' without quotes. If the dataset above had missing data, here is an example of all acceptable ways to indicate that::

   name, age, grade
   Joe, , 7
   Sally, n/a, null
   Jill, nan, 8

Use a CREATE BTABLE statement to import your data and create a new btable (bayesian table)::

    client('CREATE BTABLE mytable FROM /path/to/data.csv;')

Note that queries are not case-sensitive, and semicolons are optional.

Select Column Datatypes
~~~~~~~~~~~~~~~~~~~~~~~

After creating a btable, you will receive a message like this::

      Created btable mytable. Inferred schema:
      +-------------+-------------+-------------+
      |    name     |     age     |    grade    |
      +-------------+-------------+-------------+
      | categorical | categorical | categorical |
      +-------------+-------------+-------------+

BayesDB does its best to infer the datatype to use to model each column, but occasionally it guesses wrong (especially if the dataset is small). There are three options:

.. glossary::

   categorical
	Modeled as a categorical (multinomial) distribution. This datatype is the only choice to model non-numerical values such as strings, and does a good job of describing any discrete outcomes.

   numerical
	Modeled as a normal distribution. Only valid for numerical values.

   ignore
	Use this column type to exclude values that you wouldn't like to include in the model.

   key
        Treated by the model in the same way as ignore, but must be unique for each row, and is used to identify rows when you are selected rows. It is not required that you manually set a key: a row_id variable is automatically created as a unique row identifier. However, if using queries where you must specify particular rows, you may prefer to use a variable like 'name' to identify the row instead of its id.

In this example, BayesDB guessed that age was a categorical variable because it only observed two possible outcomes for age. However, we'd like to model age as a numerical value. In order to update the inferred datatypes, we use the UPDATE DATATYPES command::

   client('UPDATE SCHEMA FOR mytable SET age=numerical;')

Now, the updated datatypes are printed::

      Updated schema:
      +-------------+-----------+-------------+
      |    name     |    age    |    grade    |
      +-------------+-----------+-------------+
      | categorical | numerical | categorical |
      +-------------+-----------+-------------+

Run Analysis
~~~~~~~~~~~~

Now that we've chosen the correct datatypes for each of our columns, we can initialize and analyze models for our btable::

    client('INITIALIZE 20 MODELS FOR mytable;')
    client('ANALYZE mytable FOR 100 ITERATIONS;')

You may pick any number of models and iterations. More will give better quality predictions, but will take longer time before you can start querying your data.

Query your Data
~~~~~~~~~~~~~~~

Once analysis is complete, we can start running predictive queries!

First, note that BQL supports many features from normal SQL, including SELECT with LIMIT and ORDER BY::

       client('SELECT name, grade FROM mytable WHERE grade > 5 ORDER BY AGE LIMIT 10;')

Now, you can try ordering your rows by similarity to a particular row. BayesDB doesn't simply compute row-to-row similarity by using a standard distance metric (e.g. Euclidean distance), it uses CrossCat samples to estimate how similar rows are to each other. Note that we identify the row we are interested in with the value of its row_id (or other key variable, if we set one of the columns to be a key with UPDATE SCHEMA above)::

       client('SELECT name, grade FROM mytable WHERE grade > 5 ORDER BY SIMILARITY TO 1 LIMIT 10;')


Infer Missing Data
~~~~~~~~~~~~~~~~~~

You can use INFER statements to query missing values in your data. BayesDB fills the values in with its best estimate, based on its CrossCat samples::

    client('INFER grade FROM mytable WITH CONFIDENCE 0.8')

INFER statements take an optional argument, WITH CONFIDENCE, that tells INFER to only fill in a missing value if it believes it will be correct with that probability.
    
Simulate New Data
~~~~~~~~~~~~~~~~~

BayesDB can also use CrossCat's underlying model of the joint distribution of the data to simulate new data points (rows) that have similar properties as the rest of the dataset::

	client('SIMULATE grade FROM mytable WHERE age=7')

For example, the above command could be used to get a good idea of the distribution of grades BayesDB learned that 7 year olds are in.

Estimate Column Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BayesDB can estimate which columns depend on each other::

	client('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM mytable')

ESTIMATE PAIRWISE generates a column by column table that displays the value of a some function of two columns, for each pair of two columns. In this case the function we chose to use is DEPENDENCE PROBABILITY, which computes the probability that two columns are statistically dependent.

Summarize Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While SELECT, INFER, and SIMULATE return rows at the level of the unit of observation, it's useful to summarize output across rows. BayesDB can summarize output for all columns returned in a query with the SUMMARIZE statement::

  client('SUMMARIZE SELECT grade FROM mytable')

SUMMARIZE works for both discrete and continuous columns, and will calculate all summary stats that are returned from running pandas.Series.describe on each column of the data::

  client('SUMMARIZE SELECT age, grade FROM mytable')

The returned output is a table of summary statistics, with the first column showing which statistic is contained in each row.

Output to pandas.DataFrame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For users who prefer to make BayesDB queries and then continue with analysis in pandas, output can be returned as a pandas.DataFrame object. First, set the argument ``pretty=False`` to bypass pretty-printing, which will then default to returning a list of output with one element per submitted BQL statement. If only one statement is submitted, select element 0 of the list::

  pandas_df = client('SUMMARIZE SELECT grade FROM mytable', pretty=False)[0]
