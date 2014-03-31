#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Jay Baxter and Dan Lovell
#   Authors: Jay Baxter, Dan Lovell, Baxter Eaves, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

from pyparsing import *

## Matches any white space and stores it as a single space
single_white = White().setParseAction(replaceWith(' '))

## basic keywords
and_keyword = CaselessKeyword("and")
from_keyword = CaselessKeyword("from")
for_keyword = CaselessKeyword("for")
into_keyword = CaselessKeyword("into")
of_keyword = CaselessKeyword("of")
with_keyword = CaselessKeyword("with")
help_keyword = CaselessKeyword("help")
to_keyword = CaselessKeyword('to')
## Many basic keywords will never be used alone
## creating them separately like this allows for simpler whitespace and case flexibility
create_keyword = CaselessKeyword("create")
execute_keyword = CaselessKeyword("execute")
file_keyword = CaselessKeyword("file")
update_keyword = CaselessKeyword("update")
schema_keyword = CaselessKeyword("schema")
initialize_keyword = CaselessKeyword("initialize")
analyze_keyword = CaselessKeyword("analyze")
index_keyword = CaselessKeyword("index")
save_keyword = CaselessKeyword("save")
load_keyword = CaselessKeyword("load")
show_keyword = CaselessKeyword("show")
select_keyword = CaselessKeyword("select")
infer_keyword = CaselessKeyword("infer")
simulate_keyword = CaselessKeyword("simulate")
estimate_keyword = CaselessKeyword("estimate")
pairwise_keyword = CaselessKeyword("pairwise")
where_keyword = CaselessKeyword("where")
order_keyword = CaselessKeyword("order")
by_keyword = CaselessKeyword("by")
limit_keyword = CaselessKeyword("limit")
confidence_keyword = CaselessKeyword("confidence")
times_keyword = CaselessKeyword("times")
dependence_keyword = CaselessKeyword("dependence")
probability_keyword = CaselessKeyword("probability")
correlation_keyword = CaselessKeyword("correlation")
mutual_keyword = CaselessKeyword("mutual")
information_keyword = CaselessKeyword("information")
typicality_keyword = CaselessKeyword("typicality")
as_keyword = CaselessKeyword("as")
show_keyword = CaselessKeyword("show")
similarity_keyword = CaselessKeyword("similarity")
respect_keyword = CaselessKeyword("respect")
predictive_keyword = CaselessKeyword("predictive")
group_keyword = CaselessKeyword("group")
## Single and plural keywords
single_model_keyword = CaselessKeyword("model")
multiple_models_keyword = CaselessKeyword("models")
single_iteration_keyword = CaselessKeyword("iteration")
multiple_iterations_keyword = CaselessKeyword("iterations")
single_sample_keyword = CaselessKeyword("sample")
multiple_samples_keyword = CaselessKeyword("samples")
single_column_keyword = CaselessKeyword("column")
multiple_columns_keyword = CaselessKeyword("columns")
single_list_keyword = CaselessKeyword("list")
multiple_lists_keyword = CaselessKeyword("lists")
single_btable_keyword = CaselessKeyword("btable")
multiple_btable_keyword = CaselessKeyword("btables")
## Plural agnostic syntax, setParseAction makes it all display the singular
model_keyword = single_model_keyword | multiple_models_keyword
model_keyword.setParseAction(replaceWith("model"))
iteration_keyword = single_iteration_keyword | multiple_iterations_keyword
iteration_keyword.setParseAction(replaceWith("iteration"))
sample_keyword = single_sample_keyword | multiple_samples_keyword
sample_keyword.setParseAction(replaceWith("sample"))
column_keyword = single_column_keyword | multiple_columns_keyword
column_keyword.setParseAction(replaceWith("column"))
list_keyword = single_list_keyword | multiple_lists_keyword
list_keyword.setParseAction(replaceWith("list"))
btable_keyword = single_btable_keyword | multiple_btable_keyword
btable_keyword.setParseAction(replaceWith("btable"))

## Composite keywords: Inseparable elements that can have whitespace
## Using single_white and Combine to make them one string
execute_file_keyword = Combine(execute_keyword + single_white + file_keyword)
create_btable_keyword = Combine(create_keyword + single_white + btable_keyword)
update_schema_for_keyword = Combine(update_keyword + single_white + schema_keyword + single_white + for_keyword)
models_for_keyword = Combine(model_keyword + single_white + for_keyword)
model_index_keyword = Combine(model_keyword + single_white + index_keyword)
load_model_keyword = Combine(load_keyword + single_white + model_keyword)
save_model_keyword = Combine(save_keyword + single_white + model_keyword)
save_to_keyword = Combine(save_keyword + single_white + to_keyword)
list_btables_keyword = Combine(list_keyword + single_white + btable_keyword)
show_schema_for_keyword = Combine(show_keyword + single_white + schema_keyword + single_white + for_keyword)
show_models_for_keyword = Combine(show_keyword + single_white + model_keyword + single_white + for_keyword)
estimate_pairwise_keyword = Combine(estimate_keyword + single_white + pairwise_keyword)
with_confidence_keyword = Combine(with_keyword + single_white + confidence_keyword)
dependence_probability_keyword = Combine(dependence_keyword + single_white + probability_keyword)
mutual_information_keyword = Combine(mutual_keyword + single_white + information_keyword)
estimate_columns_from_keyword = Combine(estimate_keyword + single_white + column_keyword + single_white + from_keyword)
column_lists_keyword = Combine(column_keyword + single_white + list_keyword)
similarity_to_keyword = Combine(similarity_keyword + single_white + to_keyword)
with_respect_to_keyword = Combine(with_keyword + single_white + respect_keyword + single_white + to_keyword)
probability_of_keyword = Combine(probability_keyword + single_white + of_keyword)
predictive_probability_of_keyword = Combine(predictive_keyword + single_white + probability_of_keyword)

## Values/Literals
float_number = Regex(r'[-+]?[0-9]*\.?[0-9]+')
int_number = Word(nums)
operation_literal = oneOf("<= >= = < >")
equal_literal = Literal("=")
column_identifier = Word(alphas, alphanums + "_")
# single and double quotes inside value must be escaped. 
value = QuotedString('"', escChar='\\') | QuotedString("'", escChar='\\') | Word(printables)| float_number

## Functions

## Clauses

print "end"
