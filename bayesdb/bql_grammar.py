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
## uses the module pyparsing. This document provides a very good explanation of pyparsing: 
## http://www.nmt.edu/tcc/help/pubs/pyparsing/pyparsing.pdf

## Matches any white space and stores it as a single space
single_white = White().setParseAction(replaceWith(' '))

## basic keywords
and_keyword = CaselessKeyword("and")
from_keyword = CaselessKeyword("from")
for_keyword = CaselessKeyword("for")
into_keyword = CaselessKeyword("into")
of_keyword = CaselessKeyword("of")
with_keyword = CaselessKeyword("with")
help_keyword = CaselessKeyword("help").setResultsName("statement_id")
quit_keyword = CaselessKeyword("quit").setResultsName("statement_id")
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
initialize_keyword = CaselessKeyword("initialize").setResultsName("statement_id")
analyze_keyword = CaselessKeyword("analyze").setResultsName("statement_id")
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
summarize_keyword = CaselessKeyword("summarize").setResultsName("summarize")
plot_keyword = CaselessKeyword("plot").setResultsName("plot")
connected_keyword = CaselessKeyword("connected")
components_keyword = CaselessKeyword("components")
threshold_keyword = CaselessKeyword("threshold")
row_keyword = CaselessKeyword("row")
key_keyword = CaselessKeyword("key")
in_keyword = CaselessKeyword("in")
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
execute_file_keyword = Combine(execute_keyword + single_white + file_keyword).setResultsName("statement_id")
create_btable_keyword = Combine(create_keyword + single_white + btable_keyword).setResultsName("statement_id")
update_schema_for_keyword = Combine(update_keyword + single_white + 
                                    schema_keyword + single_white + for_keyword).setResultsName("statement_id")
models_for_keyword = Combine(model_keyword + single_white + for_keyword)
model_index_keyword = Combine(model_keyword + single_white + index_keyword)
load_model_keyword = Combine(load_keyword + single_white + model_keyword).setResultsName("statement_id")
save_model_keyword = Combine(save_keyword + single_white + model_keyword).setResultsName("statement_id")
save_to_keyword = Combine(save_keyword + single_white + to_keyword).setResultsName("statement_id")
list_btables_keyword = Combine(list_keyword + single_white + btable_keyword).setResultsName("statement_id")
drop_btable_keyword = Combine(drop_keyword + single_white + btable_keyword).setResultsName("statement_id")
drop_model_keyword = Combine(drop_keyword + single_white + model_keyword).setResultsName("statement_id")
show_schema_for_keyword = Combine(show_keyword + single_white + schema_keyword + 
                                  single_white + for_keyword).setResultsName("statement_id")
show_models_for_keyword = Combine(show_keyword + single_white + model_keyword + 
                                  single_white + for_keyword).setResultsName("statement_id")
show_diagnostics_for_keyword = Combine(show_keyword + single_white + diagnostics_keyword + 
                                       single_white + for_keyword).setResultsName("statement_id")
show_column_lists_for_keyword = Combine(show_keyword + single_white + column_keyword + 
                                        single_white + list_keyword + 
                                        single_white + for_keyword).setResultsName("statement_id")
show_columns_for_keyword = Combine(show_keyword + single_white + column_keyword + 
                                   single_white + for_keyword).setResultsName("statement_id")
show_row_lists_for_keyword = Combine(show_keyword + single_white + row_keyword + 
                                 single_white + list_keyword + 
                                 single_white + for_keyword).setResultsName("statement_id")
estimate_pairwise_keyword = Combine(estimate_keyword + single_white + 
                                    pairwise_keyword).setResultsName("statement_id")
estimate_pairwise_row_keyword = Combine(estimate_keyword + single_white + pairwise_keyword + 
                                        single_white + row_keyword).setResultsName("statement_id")
row_similarity_keyword = Combine(row_keyword + single_white + similarity_keyword)
with_confidence_keyword = Combine(with_keyword + single_white + confidence_keyword)
order_by_keyword = Combine(order_keyword + single_white + by_keyword)
dependence_probability_keyword = Combine(dependence_keyword + single_white + probability_keyword)
mutual_information_keyword = Combine(mutual_keyword + single_white + information_keyword)
estimate_columns_from_keyword = Combine(estimate_keyword + single_white + column_keyword + 
                                        single_white + from_keyword).setResultsName("statement_id")
estimate_columns_keyword = Combine(estimate_keyword + single_white + column_keyword).setResultsName("statement_id")
column_lists_keyword = Combine(column_keyword + single_white + list_keyword)
similarity_to_keyword = Combine(similarity_keyword + single_white + to_keyword).setResultsName("statement_id")
with_respect_to_keyword = Combine(with_keyword + single_white + respect_keyword + single_white + to_keyword)
probability_of_keyword = Combine(probability_keyword + single_white + of_keyword)
typicality_of_keyword = Combine(typicality_keyword + single_white + of_keyword)
predictive_probability_of_keyword = Combine(predictive_keyword + single_white + probability_keyword + single_white + of_keyword)
save_connected_components_with_threshold_keyword = Combine(save_keyword + single_white + 
                                                           connected_keyword + single_white + 
                                                           components_keyword + single_white + 
                                                           with_keyword + single_white + 
                                                           threshold_keyword)
save_connected_components_keyword = save_connected_components_with_threshold_keyword
key_in_keyword = Combine(key_keyword + single_white + in_keyword)

## Values/Literals
sub_query = QuotedString("(",endQuoteChar=")").setResultsName('sub_query')
float_number = Regex(r'[-+]?[0-9]*\.?[0-9]+') | sub_query#TODO setParseAction to float/int
int_number = Word(nums) | sub_query
operation_literal = oneOf("<= >= = < >")
equal_literal = Literal("=")
semicolon_literal = Literal(";")
comma_literal = Literal(",")
hyphen_literal = Literal("-")
all_column_literal = Literal('*')
identifier = (Word(alphas, alphanums + "_.").setParseAction(downcaseTokens)) | sub_query
btable = identifier.setResultsName("btable") | sub_query
# single and double quotes inside value must be escaped. 
value = (QuotedString('"', escChar='\\') | 
         QuotedString("'", escChar='\\') | 
         Word(printables)| 
         float_number | 
         sub_query)
filename = (QuotedString('"', escChar='\\') | 
            QuotedString("'", escChar='\\') | 
            Word(alphanums + "!\"/#$%&'()*+,-.:;<=>?@[\]^_`{|}~")).setResultsName("filename")
data_type_literal = categorical_keyword | numerical_keyword | ignore_keyword | key_keyword

###################################################################################
# ------------------------------------ Functions -------------------------------- #
###################################################################################

# ------------------------------- Management statements ------------------------- #

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
    print toks
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

show_for_btable_statement = ((show_schema_for_keyword | 
                              show_models_for_keyword | 
                              show_diagnostics_for_keyword | 
                              show_column_lists_for_keyword |  
                              show_columns_for_keyword | 
                              show_row_lists_for_keyword) + 
                             btable)

# LOAD MODELS <filename.pkl.gz> INTO <btable>
load_model_function = load_model_keyword + filename + Suppress(into_keyword) + btable

# SAVE MODELS FROM <btable> TO <filename.pkl.gz>
save_model_from_function = save_model_keyword + Suppress(from_keyword) + btable + Suppress(to_keyword) + filename

# DROP BTABLE <btable>
drop_btable_function = drop_btable_keyword + btable

# DROP MODEL[S] [<model_index>-<model_index>] FROM <btable>
drop_model_function = drop_keyword.setParseAction(replaceWith("drop model")).setResultsName("statement_id") + model_index_clause + Suppress(from_keyword) + btable

help_function = help_keyword
quit_function = quit_keyword

management_query = (create_btable_function | 
                      update_schema_for_function | 
                      execute_file_function | 
                      initialize_function | 
                      analyze_function | 
                      list_btables_function | 
                      show_for_btable_statement | 
                      load_model_function | 
                      save_model_from_function | 
                      drop_btable_function | 
                      drop_model_function | 
                      help_function | 
                      quit_function)

# ------------------------------ Helper Clauses --------------------------- #

# Rows can be identified either by an integer or <column> = <value> where value is unique for the given column
row_clause = (int_number.setResultsName("row_id") | 
              (identifier.setResultsName("column") + 
               Suppress(equal_literal) + 
               value.setResultsName("column_value")))

column_list_clause = Group((identifier | all_column_literal) + 
                           ZeroOrMore(Suppress(comma_literal) + 
                                      (identifier | all_column_literal))).setResultsName("column_list")

# SAVE TO <file>
save_to_clause = save_to_keyword + filename

# WITH CONFIDENCE <confidence>
with_confidence_clause = with_confidence_keyword + float_number.setResultsName("confidence")


# -------------------------------- Functions ------------------------------ #

# SIMILARITY TO <row> [WITH RESPECT TO <column>]
similarity_to_function = (Group(similarity_to_keyword.setResultsName('function_id') + 
                                row_clause + 
                                Optional(with_respect_to_keyword + column_list_clause)
                                .setResultsName('with_respect_to'))
                          .setResultsName("function")) # todo more names less indexes

# TYPICALITY
typicality_function = Group(typicality_keyword.setResultsName('function_id')).setResultsName('function')

typicality_of_function = Group(typicality_of_keyword.setResultsName("function_id") + 
                                           identifier.setResultsName("column")).setResultsName("function")

# Functions of two columns for use in dependence probability, mutual information, correlation
functions_of_two_columns_subclause = ((Suppress(with_keyword) + 
                                       identifier.setResultsName("with_column")) | 
                                      (Suppress(of_keyword) + 
                                       identifier.setResultsName("of_column") + 
                                       Suppress(with_keyword) + 
                                       identifier.setResultsName("with_column")))

# DEPENDENCE PROBABILITY (WITH <column> | OF <column1> WITH <column2>)
dependence_probability_function = Group(dependence_probability_keyword.setResultsName('function_id') + 
                                        functions_of_two_columns_subclause).setResultsName("function")

# MUTUAL INFORMATION [OF <column1> WITH <column2>]
mutual_information_function = Group(mutual_information_keyword.setResultsName('function_id') + 
                                    functions_of_two_columns_subclause).setResultsName("function")

# CORRELATION [OF <column1> WITH <column2>]
correlation_function = Group(correlation_keyword.setResultsName('function_id') + 
                             functions_of_two_columns_subclause).setResultsName("function")


# PROBABILITY OF <column>=<value>
probability_of_function = Group((probability_of_keyword.setResultsName("function_id") + 
                                 identifier.setResultsName("column") + 
                                 Suppress(equal_literal) + 
                                 value.setResultsName("value"))).setResultsName('function')

# PREDICTIVE PROBABILITY OF <column>
predictive_probability_of_function = Group(predictive_probability_of_keyword.setResultsName("function_id") + 
                                           identifier.setResultsName("column")).setResultsName("function")

# KEY IN <row_list>
key_in_rowlist_clause = Group(key_in_keyword.setResultsName("function_id") + identifier.setResultsName("row_list")).setResultsName('function')

non_aggregate_function = similarity_to_function | typicality_function | predictive_probability_of_function | Group(identifier.setResultsName('column'))

# -------------------------------- other clauses --------------------------- #

# ORDER BY <column|non-aggregate-function>[<column|function>...]
order_by_clause = Group(order_by_keyword + Group((non_aggregate_function) + ZeroOrMore(Suppress(comma_literal) + (non_aggregate_function))).setResultsName("order_by_set")).setResultsName('order_by')

# WHERE <whereclause>
single_where_condition = Group(((non_aggregate_function.setResultsName('function') + 
                                 operation_literal.setResultsName('operation') + 
                                 value.setResultsName('value')) | key_in_rowlist_clause) + 
                               Optional(with_confidence_clause))

where_clause = (where_keyword.setResultsName('where_keyword') + 
                Group(single_where_condition + 
                      ZeroOrMore(Suppress(and_keyword) + single_where_condition))
                .setResultsName("where_conditions"))

save_connected_components_clause = Group(save_connected_components_keyword
                                         .setResultsName("save_connected_components") + 
                                         float_number.setResultsName("threshold") + 
                                         ((as_keyword + 
                                           identifier.setResultsName('as_label')) | 
                                          (into_keyword + 
                                           identifier.setResultsName('into_label')))).setResultsName('connected_components_clause')

row_list_clause = Group(int_number + 
                           ZeroOrMore(Suppress(comma_literal) + 
                                      int_number)).setResultsName("row_list")

# ----------------------------- Master Query Syntax ---------------------------------------- #

query_id = (select_keyword | 
            infer_keyword | 
            simulate_keyword | 
            estimate_pairwise_keyword |
            estimate_keyword).setResultsName('statement_id')

function_in_query = (predictive_probability_of_function | 
                     probability_of_function | 
                     typicality_of_function | 
                     typicality_function | 
                     similarity_to_function |
                     dependence_probability_function | 
                     mutual_information_function | 
                     correlation_function | 
                     row_similarity_keyword |
                     similarity_keyword |
                     column_keyword |
                     Group(column_list_clause.setResultsName("columns"))).setResultsName("function")

functions_clause = Group(function_in_query + 
                         ZeroOrMore(Suppress(comma_literal) + 
                                    function_in_query)).setResultsName('functions')

query = (Optional(summarize_keyword | plot_keyword) +
         query_id + 
         functions_clause + 
         Suppress(from_keyword) + 
         btable + 
         Optional(where_clause) + 
         Each(Optional(order_by_clause) + 
              Optional(with_confidence_clause) + 
              Optional(Suppress(with_keyword) + int_number.setResultsName('samples') + Suppress(sample_keyword)) + 
              Optional(Suppress(limit_keyword) + int_number.setResultsName("limit")) + 
              Optional(for_keyword + column_list_clause.setResultsName('columns')) +
              Optional(for_keyword + row_list_clause.setResultsName('rows')) + 
              Optional(Suppress(save_to_keyword) + filename) + 
              Optional(save_connected_components_clause) + 
              Optional(Suppress(times_keyword) + int_number.setResultsName("times")) + 
              Optional(Suppress(as_keyword) + identifier.setResultsName("as_column_list"))))


bql_statement = query | management_query
