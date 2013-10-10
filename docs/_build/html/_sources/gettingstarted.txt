Getting Started
===============
This document is a quick tutorial to get you started loading your own data into BayesDB and running a few queries on it.

See the :doc:`bql` for more detailed information on BQL queries, or check out :doc:`examples` for in-depth sample data analyses that were done using BayesDB.


Create a Client
~~~~~~~~~~~~~~~

In Python (either at a prompt, or in your own module), create a Client::

     from bayesdb.Client import Client
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

In this example, BayesDB guessed that age was a categorical variable because it only observed two possible outcomes for age. However, we'd like to model age as a numerical value. In order to update the inferred datatypes, we use the UPDATE DATATYPES command::

   client('UPDATE DATATYPES FROM mytable SET age=numerical;')

Now, the updated datatypes are printed::

      Updated schema:
      +-------------+-----------+-------------+
      |    name     |    age    |    grade    |
      +-------------+-----------+-------------+
      | categorical | numerical | categorical |
      +-------------+-----------+-------------+

Run Analysis
~~~~~~~~~~~~

Now that we've chosen the correct datatypes for each of our columns, we can create and analyze models for our btable::

    client('CREATE 20 MODELS FOR mytable;')
    client('ANALYZE mytable FOR 100 ITERATIONS;')

You may pick any number of models and iterations. More will give better quality predictions, but will take longer time before you can start querying your data.

Query your Data
~~~~~~~~~~~~~~~

Once analysis is complete, we can start running predictive queries!

First, note that BQL supports many features from normal SQL, including SELECT with LIMIT and ORDER BY::

       client('SELECT name, grade FROM mytable WHERE grade > 5 ORDER BY AGE LIMIT 10;')

Now, you can try ordering your rows by similarity to a particular row. BayesDB doesn't simply compute row-to-row similarity by using a standard distance metric (e.g. Euclidean distance), it uses CrossCat samples to estimate how similar rows are to each other::

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

	client('ESTIMATE DEPENDENCE PROBABILITIES FROM mytable')

Estimate dependence probabilities generates a column by column table that illustrates how dependent each pair of columns is.
