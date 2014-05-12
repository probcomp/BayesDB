Bayesian Query Language (BQL)
==================================
Bayesian Query Language is a SQL-like language that adds support for running inference and executing predictive queries based on a bayesian model of the data.

Loading data
~~~~~~~~~~~~

::
   
   CREATE BTABLE <btable> FROM <filename.csv>

Creates a btable by importing data from the specified CSV file. The file must be in CSV format, and the first line must be a header indicating the names of each column.

::

   from bayesdb.client import Client
   c = Client()
   c('CREATE BTABLE <btable> FROM PANDAS', pandas_df=my_dataframe)

If you don't have a csv of your dataset, but you have a Pandas dataframe in Python, you can create a btable from a pandas DataFrame object by using the BayesDB Python Client. The dataframe must be passed as an additional argument to the client, as shown above.

::

   UPDATE SCHEMA FOR <btable> SET <col1>=<type1>[,<col2>=<type2>...]

Types are categorical (multinomial), numerical (continuous), ignore, and key. “Key” types are ignored for inference, but can be used lower to uniquely identify rows instead of using ID. Note that datatypes cannot be updated once the model has been analyzed.

::
   
   EXECUTE FILE <filename.bql>

You may write BQL commands in a file and run them all at once by use EXECUTE FILE and passing your .bql file. This is especially handy with UPDATE SCHEMA for tables with many columns, where you may want to write a long, cumbersome UPDATE SCHEMA query in a separate file to preserve it.

Initializing models and running analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
It is necessary to run INITIALIZE MODELS and ANALYZE in order for BayesDB to evaluate any query involving any predictions. The models that this command creates can be thought of as possible explanations for the underlying structure of the data in a Bayesian probability model. In order to generate reasonable predictions, it is recommended that a minimum of about 32 models should be initialized, and each model should be analyzed for a minimum of about 250 iterations. The more models you create, the higher quality your predictions will be, so if it is computationally feasible to initialize and analyze 128 or 256 models for your dataset, it is highly recommended. It is sensible to use 250-500 iterations of analyze for each model, no matter how many models you have.

::

	INITIALIZE <num_models> MODELS FOR <btable> [WITH CONFIG <config>]

Initializes <num_models> models. 

Available models include "naive bayes" and "crp mixture"

::

	ANALYZE <btable> [MODEL[S] <model_index>-<model_index>] FOR (<num_iterations> ITERATIONS | <seconds> SECONDS)

Analyze the specified models for the specified number of iterations (by default, analyze all models).

Examining the state of your btables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
There are a few convenience commands available to help you view the internal state of BayesDB::
   
   LIST BTABLES

View the list of all btable names in BayesDB.

::

   SHOW SCHEMA FOR <btable>

View each column name, and each column's datatype.

::

   SHOW MODELS FOR <btable>

Display all models, their ids, and how many iterations of ANALYZE have been performed on each one.

::

   SHOW DIAGNOSTICS FOR <btable>

Advanced feature: show diagnostic information for your btable's models.

Saving and loading models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Save and load models allow you to export your models from one instance of BayesDB (save), and then import them back into any instance of BayesDB (load), so that you don't have to re-run the potentially time-consuming ANALYZE step.   

::

   LOAD MODELS <filename.pkl.gz> INTO <btable>

::

   SAVE MODELS FROM <btable> TO <filename.pkl.gz>
   

Deleting
~~~~~~~~
You may delete an entire btable (including all its associated models - careful!), or just some of the models.

::

	DROP BTABLE <btable>

::

	DROP MODEL[S] [<model_index>-<model_index>] FROM <btable>

Querying
~~~~~~~~
BayesDB has five fundamental query statements: SELECT, INFER, SIMULATE, ESTIMATE COLUMNS, and ESTIMATE PAIRWISE. They bear a strong resemblance to SQL queries.

SELECT is just like SQL's SELECT, except in addition to selecting, filtering (with where), and ordering raw column values, you may also use predictive functions in any of those clauses::

   SELECT <columns|functions> FROM <btable> [WHERE <whereclause>] [ORDER BY <columns|functions>] [LIMIT <limit>]

INFER is just like SELECT, except that it also tries to fill in missing values. The user may specify the desired confidence level to use (a number between 0 and 1, where 0 means "fill in every missing value with whatever your best guess is", and 1 means "only fill in a missing value if you're sure what it is"). If confidence is not specified, 0 is chosen as default. Optionally, the user may specify the number of samples to use when filling in missing values: the default value is good in general, but if you know what you're doing and want higher accuracy, you can increase the numer of samples used::

   INFER <columns|functions> FROM <btable> [WHERE <whereclause>] [WITH CONFIDENCE <confidence>] [WITH <numsamples> SAMPLES] [ORDER BY <columns|functions>] [LIMIT <limit>]

SIMULATE generates new rows from the underlying probability model a specified number of times::

   SIMULATE [HIST] <columns> FROM <btable> [WHERE <whereclause>] [GIVEN <column>=<value>] TIMES <times> [SAVE TO <file>]

ESTIMATE COLUMNS is like a SELECT statement, but lets you select columns instead of rows::

   ESTIMATE COLUMNS FROM <btable> [WHERE <whereclause>] [ORDER BY <functions>] [LIMIT <limit>] [AS <column_list>]
   
With ESTIMATE PAIRWISE, you may use any function that takes two columns as input, i.e. DEPENDENCE PROBABILITY, CORRELATION, or MUTUAL INFORMATION, and generates a matrix showing the value of that function applied to each pair of columns. See the :ref:`functions` section for more information.

In addition, you may also add "SAVE CONNECTED COMPONENTS WITH THRESHOLD <threshold> AS <column_list>" in order to compute groups of columns, where the value of the pairwise function is at least <threshold> between at least one pair of columns in the group. Then, those groups of columns are saved as column lists with names "column_list_<id>", where id is an integer starting with 0::

   ESTIMATE PAIRWISE <function> FROM <btable> [FOR <columns>] [SAVE TO <file>] [SAVE CONNECTED COMPONENTS WITH THRESHOLD <threshold> AS <column_list>]

You may also compute pairwise functions of rows with ESTIMATE PAIRWISE ROW::

  ESTIMATE PAIRWISE ROW SIMILARITY FROM <btable> [FOR <rows>] [SAVE TO <file>] [SAVE CONNECTED COMPONENTS WITH THRESHOLD <threshold> [INTO|AS] <btable>]

In the above query specifications, you may be wondering what some of the notation, such as <columns|functions> and <whereclause>, means. <columns|functions> just means a list of comma-separated column names or function specifications::

  SELECT name, age, date FROM...
  SELECT name, TYPICALITY, age, date FROM...

<whereclause> specifies an AND-separated list of <column|function> <operator> <value>, where operator must be one of (=, <, <=, >, >=)::

  SELECT * FROM table WHERE name = 'Bob' AND age <= 18 AND TYPICALITY > 0.5 ....

Query Modifiers
~~~~~~~~~~~~~~~

SUMMARIZE or PLOT may be prepended to any query that returns table-formatted output (almost every query) in order to return a summary of the data table instead of the raw data itself. This is extremely useful as a tool to quickly understand a huge result set: it quickly becomes impossible to see trends in data by eye without the assistance of SUMMARIZE or PLOT.

SUMMARIZE displays summary statistics of each of the output columns: for numerical data, it displays information like the mean, standard deviation, min, and max, and for categorical data it displays the most common values and their probabilities::

  SUMMARIZE SELECT * FROM table...

PLOT displays plots of the marginal distributions of every single output column, as well as the joint distributions of every pair of output columns. PLOT displays a heat map for pairs of numerical columns, the exact joint distribution for pairs of categorical columns, and a series of box plots for mixed numerical/categorical data. Many tools, like R and pandas, have functionality similar to PLOT when all the data is the same type, but PLOT is specially designed and implemented from the ground up to behave well with mixed datatypes::

  PLOT SELECT * FROM table...


Column Lists
~~~~~~~~~~~~
Instead of manually typing in a comma-separated list of columns for queries, you may instead use a 'column list' in any query that asks for a list of columns. Column lists are created with ESTIMATE COLUMNS, which allows you to filter the columns you want included with a where clause, order the columns by some function, limit the number of columns, and save the column list by giving it a name with the AS clause::
   
   ESTIMATE COLUMNS FROM <btable> [WHERE <whereclause>] [ORDER BY <functions>] [LIMIT <limit>] [AS <column_list>]

Since it may be hard to see example what you'd put in the WHERE or ORDER by clause, take a look at an example, and be sure to read the :ref:`functions` section below::

  ESTIMATE COLUMNS FROM table WHERE TYPICALITY > 0.6 ORDER BY DEPENDENCE PROBABILITY WITH name;  

You can print out the names of the stored column lists in your btable with::

   SHOW COLUMN LISTS FOR <btable>

And you can view the columns in a given column list or table with::

   SHOW COLUMNS FOR <column_list|btable>

Row Lists
~~~~~~~~~
In addition to storing lists of columns, BayesDB also allows you to store lists of rows. Currently, the only way to create row lists is by running ESTIMATE PAIRWISE ROW SIMILARITY with SAVE CONNECTED COMPONENTS. The components will be saved as row lists, which you can then view with the following command::

    SHOW ROW LISTS FOR <table>

To execute a query only on rows that are in a specific row list, just add the following predicate to any WHERE clause in a SELECT or INFER statment::

    WHERE key in <row_list>


.. _functions:

Predictive Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functions of rows:
^^^^^^^^^^^^^^^^^^
Functions that take a row as input may be used in many types of queries, including::

  SELECT
  INFER
  ORDER BY (except in ESTIMATE COLUMNS)
  WHERE (except in ESTIMATE COLUMNS)
  
Functions in this category include::

   SIMILARITY TO <row> [WITH RESPECT TO <column>]

Similarity measures the similarity between two rows. This can be interpreted by thinking of dividing the rows up into clusters, and measuring how likely it would be that these two rows would be in the same cluster. By default, similarity considers all columns when deciding how similar to rows are, but you may optionally specify a specifiic column to compute similarity with respect to.

::

   TYPICALITY

The typicality of a row measures how similar to other rows this row is. If a row is more dependent, on average, with other rows, then it becomes more typical.

::
   
   PROBABILITY OF <column>=<value>

The probability of a cell taking on a particular value is the probability that the Bayesian probability model assigns to this particular outcome.

::

   PREDICTIVE PROBABILITY OF <column>

The predictive probability of a value is similar to the "PROBABILITY OF <column>=<value>" query, but it measures the probability that each cell takes on its observed value, as opposed to a specific value that the user specifies.


Here are some examples::

  SELECT SIMILARITY TO 0 WITH RESPECT TO name, TYPICALITY FROM btable WHERE PROBABILITY OF name='Bob' > 0.8 ORDER BY PREDICTIVE PROBABILITY OF name;

Functions of two columns
^^^^^^^^^^^^^^^^^^^^^^^^
Functions of two columns may be used in the following queries::

  ESTIMATE PAIRWISE (omit the 'OF' clause)
  SELECT (include the 'OF' clause; they only return one row)  

Here are the three functions::  
      
  DEPENDENCE PROBABILITY [OF <column1>] WITH <column2>

The dependence probability between two columns is a measure of how likely it is that the two columns are dependent (opposite of indepdendent). Note that this does not measure the strength of the relationship between the two columns; it merely measures the probability that there is any relationship at all.
  
::
   
  MUTUAL INFORMATION [OF <column1>] WITH <column2>

Mutual information between two columns measures how much information a value in one column gives you about the value in the other column. If mutual information is 0, then knowing the first column tells you nothing about the other column (they are independent). Mutual information is always nonnegative, and is measured in bits.

::

  CORRELATION [OF <column1>] WITH <column2>

This is the standard Pearson correlation coefficient between the two columns. All rows with missing values in either or both of the two columns will be removed before calculating the correlation coefficient.

Here are some examples::

  ESTIMATE PAIRWISE DEPENDENCE PROBABILITY OF name WITH age;
  SELECT MUTUAL INFORMATION OF name WITH age FROM table...


Functions of one column, for SELECT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Functions in this category take one column as input, and can only be used in::

  SELECT (but they only return one row)

There is only one function like this::

  TYPICALITY OF <column>

The typicality of a column measures how similar to other columns this column is. If a column is more dependent, on average, with other columns, then it becomes more typical.

Here is an example::

  SELECT TYPICALITY OF age FROM...

Functions of one column, for ESTIMATE COLUMNS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For each of the functions of one or two columns above (that were usable in SELECT, and sometimes ESTIMATE PAIRWISE), there is a version of the function that is usable in ESTIMATE COLUMNS, in the following clauses::

  WHERE (in ESTIMATE COLUMNS only)
  ORDER BY (in ESTIMATE COLUMNS only)

Here are the functions::

  TYPICALITY

This is the same function as TYPICALITY OF <column> above, but the column argument is implicit.

::
   
  CORRELATION WITH <column>

This is the same function as CORRELATION OF <column1> WITH <column2> above, but one of the column arguments is implicit.  

::
   
  DEPENDENCE PROBABILITY WITH <column>

This is the same function as DEPENDENCE PROBABILITY OF <column1> WITH <column2> above, but one of the column arguments is implicit.    

::
   
  MUTUAL INFORMATION WITH <column>

This is the same function as MUTUAL INFORMATION OF <column1> WITH <column2> above, but one of the column arguments is implicit.    
   

Here are some examples::

  ESTIMATE COLUMNS FROM table WHERE TYPICALITY > 0.6 AND CORRELATION WITH name > 0.5 ORDER BY DEPENDENCE PROBABILITY WITH name;


