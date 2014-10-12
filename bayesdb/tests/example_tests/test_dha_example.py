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

# test dha_example
import pytest
import os
from bayesdb import tester as tu
from bayesdb.tester import assertIn
from bayesdb.tester import assertNotIn
from bayesdb.tester import assertLessThan


# TestClient should go in a pytest fixture. Kwargs are passed through request params.
# test fixtures must be passed 'request' in order to call the finalizer
@pytest.fixture(scope='module', params=[dict(num_models=10, num_analyze_iterations=10)])
def dha_fixture(request):
    csv_filename = '../data/dha.csv'  # csv filename required
    test_id = 'dha'  # test id required for naming
    key_column = 1  # use 'name' as key column
    tclient = tu.TestClient(test_id, csv_filename, num_models=request.param['num_models'],
                            num_analyze_iterations=request.param['num_analyze_iterations'],
                            key_column=key_column)

    # finalizer required for cleanup
    def fin():
        print ("finalizing %s" % tclient.btable_name)
        tclient.finalize()

    request.addfinalizer(fin)
    return tclient


# make sure to order tests from top to bottom
def test_dha_example_low_dependence_between_spnd_and_qual(dha_fixture):
    intro = """
    Dartmouth Atlas of Health
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    **Recording the cost structure, capacity and quality of care of US hospitals.**

    One of the main concerns in American health care is addressing unwarranted variations in quality: a disparity between the cost and outcomes of care. The cost-care disparity is well-documented mainly as a result of the Dartmouth Atlas of Health Care, a freely available dataset which

        ...uses Medicare data to provide information and analysis about national, regional, and local markets, as well as hospitals and their affiliated physicians

    These findings were the result of custom analysis by health economics and statistics researchers. Here we will see how easy it is to answer the same underlying questions using BayesDB.

    Unwarranted variations in aggregate
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    First, we create a btable intialize, and analyze models,
    """

    dha_fixture.comment(intro)

    comment_0 = """
    To get a sense of the probable dependencies between variables, we create a column dependence probability matrix in which each cell represents a pair of variables and the value represents the probability of their being statistically dependent under the inferred CrossCat model. Here, we have zoomed in on two variables, the first related to Medicare spending, and the second related to quality.
    """
    dha_fixture.comment(comment_0)

    z_figure_path = os.path.join(dha_fixture.dir, 'dha_z')
    out = dha_fixture('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM <btable> SAVE TO ' + z_figure_path + ';')

    comment_1 = """
    The resulting figure plots dependence probabilities of all pairs of variables as saturations in a large matrix. Dark areas represent variables with a high probability of dependence, light areas indicate a low probability of dependence. This contains quite a bit more information than we need, so we select out the rows that correspond to two variables that represent our question of interest: Medicare spending on ambulances and quality of care.

    .. image:: %s
   :width: 1000px

   Notice that quality and cost show no dependence. We can list the variables that probably have a dependence on spending, again focusing on Medicare spending on ambulances.
    """ % (z_figure_path)
    dha_fixture.comment(comment_1)

    colnames = out['column_names'].tolist()
    index_mdcr_spnd_amblnc = colnames.index('mdcr_spnd_amblnc')
    index_qual_score = colnames.index('qual_score')
    dependence_probability = out['matrix'][index_mdcr_spnd_amblnc, index_qual_score]

    # assert that the dependence probability between mdcr_spnd_amblnc and qual_score is less than .1
    assertLessThan(dependence_probability, .4)


def test_dha_example_spending_variables_dependent_with_mdcr_spnd_amblnc(dha_fixture):
    out = dha_fixture('ESTIMATE COLUMNS FROM <btable> ORDER BY DEPENDENCE PROBABILITY WITH mdcr_spnd_amblnc LIMIT 10;')

    assertIn('pymt_p_visit_ratio', out['column name'].values)
    assertIn('ttl_mdcr_spnd', out['column name'].values)
    assertIn('pymt_p_md_visit', out['column name'].values)
    assertIn('mdcr_spnd_inp', out['column name'].values)
    assertIn('hosp_reimb_ratio', out['column name'].values)

    assertNotIn('qual_score', out['column name'].values)
    # TODO: others?


def test_dha_example_score_variables_dependent_with_qual_score(dha_fixture):
    comment_2 = """
    Other spending variables as well as reimbursement related tend to be dependent, while quality variables do not appear on the list.

    Similarly, we can list the variables that have the highest probability of dependence with quality,
    """
    dha_fixture.comment(comment_2)

    out = dha_fixture('ESTIMATE COLUMNS FROM <btable> ORDER BY DEPENDENCE PROBABILITY WITH qual_score LIMIT 10;')

    assertIn('ami_score', out['column name'].values)
    assertIn('pneum_score', out['column name'].values)
    assertIn('chf_score', out['column name'].values)

    assertLessThan(out['dependence probability with qual_score'][5], .6)
    assertLessThan(out['dependence probability with qual_score'][6], .6)
    assertLessThan(out['dependence probability with qual_score'][7], .6)
    assertLessThan(out['dependence probability with qual_score'][8], .6)
    assertLessThan(out['dependence probability with qual_score'][9], .6)

    comment_3 = """
    The list includes other quality related scores, which have a very strong dependence. All of the remaining variables do not show strong evidence of dependence.

    Unwarranted variations on a per-town basis
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Which hospitals have surprising spending and quality levels--either unusually low or unusually high--given their other attributes?
    """
    dha_fixture.comment(comment_3)


def test_dha_example_mcallen_anomalous(dha_fixture):
    out_0 = dha_fixture('SELECT name, PREDICTIVE PROBABILITY OF mdcr_spnd_amblnc FROM <btable> ORDER BY PREDICTIVE PROBABILITY OF mdcr_spnd_amblnc ASC LIMIT 10')
    out_1 = dha_fixture('SELECT name, PREDICTIVE PROBABILITY OF qual_score FROM <btable> ORDER BY PREDICTIVE PROBABILITY OF qual_score ASC LIMIT 10')

    comment_4 = """
    McAllen TX appears on both lists as being suprising with respect to Medicare spending on ambulances and with respect to quality of care. To check this result, we might look at some more generic assessment of spending, such as the payment received per doctor's visit.
    """
    dha_fixture.comment(comment_4)

    out_2 = dha_fixture('SELECT name, PREDICTIVE PROBABILITY OF mdcr_spnd_amblnc FROM <btable> ORDER BY PREDICTIVE PROBABILITY OF mdcr_spnd_amblnc ASC LIMIT 10')

    assertIn('McAllen TX', out_0.name.values)
    assertIn('McAllen TX', out_1.name.values)
    assertIn('McAllen TX', out_2.name.values)
    # use sets to determine that ONLY McAllen is in all three lists
    assertIn('McAllen TX', set(out_0.name.values).intersection(set(out_1.name.values).intersection(set(out_2.name.values))))

    # TODO: add links
    comment_5 = """
    Only one of these hospitals, McAllen TX, appears on all three of these lists. It has also been repeatedly written up in the popular press (The NewYorker, CBS News and NPR) as an illustration of the dissociation between spending and quality of care.

    Further information
    ^^^^^^^^^^^^^^^^^^^

    The BayesDB-ready .csv and pre-computed models used here can be found in the /examples directory in the BayesDB Github Repository.

    For more information about the Dartmouth Atlas of Health Care, http://www.dartmouthatlas.org/.
    """
    dha_fixture.comment(comment_5)
