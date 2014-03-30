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

## basica keywords
operation_keyword = oneOf("<= >= = < >")
equal_keyword = Keyword("=")
and_keyword = CaselessKeyword("and")
from_keyword = CaselessKeyword("from")
for_keyword = CaselessKeyword("for")
into_keyword = CaselessKeyword("into")
of_keyword = CaselessKeyword("of")
with_keyword = CaselessKeyword("with")
help_keyword = CaselessKeyword("help")
## Many basic keywords will never be used alone
## creating them separately like this allows for simpler whitespace and case flexibility
create_keyword = CaselessKeyword("create")
btable_keyword = CaselessKeyword("btable")
execute_keyword = CaselessKeyword("execute")
file_keyword = CaselessKeyword("file")
update_keyword = CaselessKeyword("update")
schema_litearl = CaselessKeyword("schema")
initialize_keyword = CaselessKeyword("initialize")
analyze_keyword = CaselessKeyword("analyze")
index_keyword = CaselessKeyword("caseless")
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
## Plural agnostic syntax
model_keyword = single_model_keyword | multiple_models_keyword
iteration_keyword = single_iteration_keyword | multiple_iterations_keyword
sample_keyword = single_sample_keyword | multiple_iterations_keyword
column_keyword = single_column_keyword | multiple_iterations_keyword
list_keyword = single_list_keyword | multiple_lists_keyword

## Composite keywords: Inseparable elements that can have whitespace
## Using White() and Combine to make them one string
execute_file_literal = Combine(execute_keyword + White() + file_keyword)
create_btable_literal = Combine(create_keyword + White() + btable_keyword)

## Values

## Functions

## Clauses
print execute_literal.parseString("execute")
print file_literal.parseString("file")
print type(execute_file_literal.parseString("execute file")[0])


queries =["execute file", 
"exECUTE FILE"
]
for string in queries: 
    print execute_file_literal.parseString(string)

print "end"
