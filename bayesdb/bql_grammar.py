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
set_keyword = CaselessKeyword("set")
categorical_keyword = CaselessKeyword("categorical")
numerical_keyword = CaselessKeyword("numerical")
ignore_keyword = CaselessKeyword("ignore")
key_keyword = CaselessKeyword("key")
initialize_keyword = CaselessKeyword("initialize").setResultsName("function_id")
analyze_keyword = CaselessKeyword("analyze").setResultsName("function_id")
index_keyword = CaselessKeyword("index")
save_keyword = CaselessKeyword("save")
load_keyword = CaselessKeyword("load")
drop_keyword = CaselessKeyword("drop")
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
diagnostics_keyword = CaselessKeyword("diagnostics")
hist_keyword = CaselessKeyword("hist")
connected_keyword = CaselessKeyword("connected")
components_keyword = CaselessKeyword("components")
threshold_keyword = CaselessKeyword("threshold")
row_keyword = CaselessKeyword("row")
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
single_second_keyword = CaselessKeyword("second")
multiple_seconds_keyword = CaselessKeyword("seconds")
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
second_keyword = single_second_keyword | multiple_seconds_keyword
second_keyword.setParseAction(replaceWith("second"))

## Composite keywords: Inseparable elements that can have whitespace
## Using single_white and Combine to make them one string
execute_file_keyword = Combine(execute_keyword + single_white + file_keyword).setResultsName("function_id")
create_btable_keyword = Combine(create_keyword + single_white + btable_keyword).setResultsName("function_id")
update_schema_for_keyword = Combine(update_keyword + single_white + 
                                    schema_keyword + single_white + for_keyword).setResultsName("function_id")
models_for_keyword = Combine(model_keyword + single_white + for_keyword)
model_index_keyword = Combine(model_keyword + single_white + index_keyword)
load_model_keyword = Combine(load_keyword + single_white + model_keyword).setResultsName("function_id")
save_model_keyword = Combine(save_keyword + single_white + model_keyword).setResultsName("function_id")
save_to_keyword = Combine(save_keyword + single_white + to_keyword).setResultsName("function_id")
list_btables_keyword = Combine(list_keyword + single_white + btable_keyword).setResultsName("function_id")
drop_btable_keyword = Combine(drop_keyword + single_white + btable_keyword).setResultsName("function_id")
drop_model_keyword = Combine(drop_keyword + single_white + model_keyword).setResultsName("function_id")
show_schema_for_keyword = Combine(show_keyword + single_white + schema_keyword + single_white + for_keyword).setResultsName("function_id")
show_models_for_keyword = Combine(show_keyword + single_white + model_keyword + single_white + for_keyword).setResultsName("function_id")
show_diagnostics_for_keyword = Combine(show_keyword + single_white + diagnostics_keyword + single_white + for_keyword).setResultsName("function_id")
estimate_pairwise_keyword = Combine(estimate_keyword + single_white + pairwise_keyword).setResultsName("function_id")
estimate_pairwise_row_keyword = Combine(estimate_keyword + single_white + pairwise_keyword + single_white + row_keyword).setResultsName("function_id")
with_confidence_keyword = Combine(with_keyword + single_white + confidence_keyword)
dependence_probability_keyword = Combine(dependence_keyword + single_white + probability_keyword)
mutual_information_keyword = Combine(mutual_keyword + single_white + information_keyword)
estimate_columns_from_keyword = Combine(estimate_keyword + single_white + column_keyword + single_white + from_keyword).setResultsName("function_id")
column_lists_keyword = Combine(column_keyword + single_white + list_keyword)
similarity_to_keyword = Combine(similarity_keyword + single_white + to_keyword)
with_respect_to_keyword = Combine(with_keyword + single_white + respect_keyword + single_white + to_keyword)
probability_of_keyword = Combine(probability_keyword + single_white + of_keyword)
predictive_probability_of_keyword = Combine(predictive_keyword + single_white + probability_of_keyword)
save_connected_components_with_threshold_keyword = Combine(save_keyword + single_white + 
                                                           connected_keyword + single_white + 
                                                           components_keyword + single_white + 
                                                           with_keyword + single_white + threshold_keyword).setResultsName("function_id")

## Values/Literals
float_number = Regex(r'[-+]?[0-9]*\.?[0-9]+')
int_number = Word(nums)
operation_literal = oneOf("<= >= = < >")
equal_literal = Literal("=")
semicolon_literal = Literal(";")
comma_literal = Literal(",")
hyphen_literal = Literal("-")
identifier = Word(alphas, alphanums + "_.")
btable = identifier.setResultsName("btable")
# single and double quotes inside value must be escaped. 
value = QuotedString('"', escChar='\\') | QuotedString("'", escChar='\\') | Word(printables)| float_number
filename = (QuotedString('"', escChar='\\') | QuotedString("'", escChar='\\') | Word(alphanums + "!\"/#$%&'()*+,-.:;<=>?@[\]^_`{|}~")).setResultsName("filename")
data_type_literal = categorical_keyword | numerical_keyword | ignore_keyword | key_keyword

##################################################################################
# ------------------------------------ Functions --------------------------------#
##################################################################################

# ------------------------------- Management functions --------------------------#

# CREATE BTABLE <btable> FROM <filename.csv>
create_btable_function = create_btable_keyword + btable + Suppress(from_keyword) + filename

# UPDATE SCHEMA FOR <btable> SET <col1>=<type1>[,<col2>=<type2>...]
type_clause = Group(ZeroOrMore(Group(identifier + Suppress(equal_literal) + data_type_literal) + 
                               Suppress(comma_literal)) + 
                    Group(identifier + Suppress(equal_literal) + data_type_literal)).setResultsName("type_clause")
update_schema_for_function = (update_schema_for_keyword + 
                              btable + 
                              Suppress(set_keyword) + 
                              type_clause)
# EXECUTE FILE <filename.bql>
execute_file_function = execute_file_keyword + filename

# INITIALIZE <num_models> MODELS FOR <btable>
initialize_function = (initialize_keyword + int_number.setResultsName("num_models") + 
                       Suppress(models_for_keyword) + btable)

# ANALYZE <btable> [MODEL[S] <model_index>-<model_index>] FOR (<num_iterations> ITERATIONS | <seconds> SECONDS)
def list_from_index_clause(toks):
    ## takes index tokens separated by '-' for range and ',' for individual and returns a list of unique indexes
    index_list = []
    for token in toks[0]:
        if type(token)== str:
            index_list.append(int(token))
        elif len(token) == 2:
            index_list += range(int(token[0]), int(token[1])+1)
        #TODO else throw exception
        index_list.sort()
    return [list(set(index_list))]

# TODO separate out model_keyword for generic use
model_index_clause = (model_keyword + 
                      Group((Group(int_number + Suppress(hyphen_literal) + int_number) | int_number) + 
                            ZeroOrMore(Suppress(comma_literal) + 
                                       (Group(int_number + Suppress(hyphen_literal) + int_number) |
                                        int_number)))
                      .setParseAction(list_from_index_clause)
                      .setResultsName('index_list')).setResultsName('index_clause')
analyze_function = (analyze_keyword + btable + 
                    Optional(model_index_clause) + 
                    Suppress(for_keyword) + 
                    ((int_number.setResultsName('num_iterations') + iteration_keyword) | 
                     (int_number.setResultsName('num_seconds') + second_keyword)))
                    

# LIST BTABLES
list_btables_function = list_btables_keyword

# SHOW SCHEMA FOR <btable>
show_schema_for_function = show_schema_for_keyword + btable

# SHOW MODELS FOR <btable>
show_models_for_function = show_models_for_keyword + btable

# SHOW DIAGNOSTICS FOR <btable>
show_diagnostics_for_function = show_diagnostics_for_keyword + btable

# LOAD MODELS <filename.pkl.gz> INTO <btable>
load_model_function = load_model_keyword + filename + Suppress(into_keyword) + btable

# SAVE MODELS FROM <btable> TO <filename.pkl.gz>
save_model_from_function = save_model_keyword + Suppress(from_keyword) + btable + Suppress(to_keyword) + filename

# DROP BTABLE <btable>
drop_btable_function = drop_btable_keyword + btable

# DROP MODEL[S] [<model_index>-<model_index>] FROM <btable>
drop_model_function = drop_keyword.setParseAction(replaceWith("drop model")).setResultsName('function_id') + model_index_clause + Suppress(from_keyword) + btable



## Clauses
print "imported"
