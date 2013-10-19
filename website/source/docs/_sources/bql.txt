Bayesian Query Language (BQL) Spec
==================================
Bayesian Query Language is an extension of SQL that adds support for running inference and executing predictive queries based on a bayesian model of the data.

Loading data
~~~~~~~~~~~~

CREATE BTABLE
^^^^^^^^^^^^^

::

	CREATE BTABLE <btable> FROM <filename>

UPDATE DATATYPES
^^^^^^^^^^^^^^^^
	
::	

	UPDATE DATATYPES FROM <btable> SET <col1>=<type1>[,<col2>=<type2>...]

(Types are categorical (multinomial), continuous, ignore, and key. “Key” types are ignored for inference, but can be used lower to uniquely identify rows instead of using ID. Note that datatypes cannot be updated once the model has been analyzed: should it throw an error message or be more graceful?)

Creating models and running analysis (generating samples)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CREATE MODELS
^^^^^^^^^^^^^

::

	CREATE [<num_models>] MODELS FOR <btable>

ANALYZE
^^^^^^^

::

	ANALYZE <btable>
	[CHAIN INDEX[ES] <chain_index1>[,<chain_index2>,...]] (you may specify ranges)
	[FOR <num_iterations> ITERATIONS] | [FOR <num_seconds> SECONDS]

Importing and exporting samples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
IMPORT SAMPLES
^^^^^^^^^^^^^^

::

	IMPORT SAMPLES <filename> INTO <btable>

EXPORT SAMPLES
^^^^^^^^^^^^^^

::

	EXPORT SAMPLES FROM <btable> TO <filename>

Deleting
~~~~~~~~

DROP BTABLE
^^^^^^^^^^^

::

	DROP BTABLE <btable>

DELETE MODELS
^^^^^^^^^^^^^
	
::

	DELETE MODELS <chain_indexes> FROM <btable>

Querying
~~~~~~~~

SELECT
^^^^^^

::

	SELECT <columns> FROM <btable> [WHERE <whereclause>] [LIMIT <limit>] [ORDER BY <columns>]

INFER
^^^^^

::

	INFER <columns> FROM <btable> [WHERE <whereclause>] [WITH CONFIDENCE <confidence>] [LIMIT <limit>] [WITH <numsamples> SAMPLES] [ORDER 

SIMULATE
^^^^^^^^

::

	SIMULATE <columns> FROM <btable> [WHERE <whereclause>] TIMES <times> [ORDER BY <columns>]


ESTIMATE PAIRWISE DEPENDENCE STRENGTH
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

	ESTIMATE PAIRWISE DEPENDENCE STRENGTH FOR <btable>


Derived Quantities
~~~~~~~~~~~~~~~~~~

Every derived quantity that outputs a column takes row as an implicit argument; the other arguments are explicit. Every derived quantity that outputs a scalar is similar to a SQL aggregate. Derived quantities that output a column are the things that you can SELECT or ORDER BY. Quantities that output a scalar can be SELECTed, and will return the same value for every row returned, but they cannot be ORDERed BY.

To specify a row (currently similarity_to is the only derived quantity where this is necessary), either the row_id or the uniquely identifying value of the key field may be specified.


SIMILARITY TO
^^^^^^^^^^^^^

::

	similarity_to(row [, columns]): column (r, c, target_row [, target_columns] -> value). probability that the cells in this row are in the same view and category as the target row

ROW TYPICALITY
^^^^^^^^^^^^^^

::

	row_typicality: column (r -> value). typicality(row [, columns]) probability that a col is in the same category as a random other row (weighting views appropriately)


Column-aggregate derived quantities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

COLUMN CENTRALITY
^^^^^^^^^^^^^^^^^

::

	col_centrality(col): scalar (c -> value). probability that col is in the same view as a random other column (just 1 - prob_dependence averaged over all target columns)

MUTUAL INFORMATION
^^^^^^^^^^^^^^^^^^

::

	mutual_information(col1, col2): scalar (c1, c2 -> value)



