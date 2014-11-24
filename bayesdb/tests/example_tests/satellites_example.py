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

# test satellites_example
import pytest
import os
from bayesdb import tester as tu
from bayesdb.tester import assertIn
from bayesdb.tester import assertNotIn
from bayesdb.tester import assertLessThan
from bayesdb.tester import assertGreaterThan


# TestClient should go in a pytest fixture. Args can go in the fixture or can be passed through
# request like Kwargs. Test fixtures must be passed 'request' in order to call the finalizer and
# to be parameterized.
#   Here, we run one test, creating 32 models and analyzing for 500 iterations. Note that multiple
# tests can be run by adding multiple dicts to the params arg list.

@pytest.fixture(scope='module', params=[dict(num_models=32, num_analyze_iterations=300)])
def satellites_fixture(request):
    csv_filename = '../data/satellites.csv'  # csv filename required
    test_id = 'satellites'  # test id required for naming
    key_column = 0  # set key column
    tclient = tu.TestClient(test_id, csv_filename, 
                            num_models=request.param['num_models'],
                            num_analyze_iterations=request.param['num_analyze_iterations'],
                            key_column=key_column)

    # finalizer required for cleanup. This must be added before request.addfinalizer.
    def fin():
        print ("finalizing %s" % tclient.btable_name)
        tclient.finalize()

    request.addfinalizer(fin)
    return tclient


# if you divide files, prepend number to test names so they happen in order. You will also have
# to run pytest in a single process.
def test_satellites_example(satellites_fixture):
    # Multiline comments should not follow the indentation level. Only inline code should be tabbed.
    intro = """
Satellites Analysis
~~~~~~~~~~~~~~~~~~~

Man-made satellites don't present the easiest field of study, at least partly because of inaccessibility of data in the past, but also because of intangibility - these are machines we'll never see up close (hopefully!), and likely never even acknowledge until we have difficulty getting GPS reception while lost on a road trip.

The Union of Concerned Scientists (UCS) created a database of characteristics of over 1000 orbiting satellites launched by countries around the world for any number of purposes and user categories, providing a new opportunity to analyze exactly what's going on above our heads. With the data set in hand, we were interested in seeing what BayesDB could detect about relationships in the data, in the form of both confirmatory and exploratory analyses.

Credit to UCS for publishing the [satellite database](http://www.ucsusa.org/satellite_database), available at the link provided.
"""

    # Add the intro comment before any commands
    satellites_fixture.comment(intro, introduction=True)

    dependence_probability_figure_path = os.path.join(satellites_fixture.dir, 'satellites_pairwise_dependence.png')
    out = satellites_fixture('ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM <btable> SAVE TO ' + dependence_probability_figure_path + ';')

    comment_0 = """
Pairwise dependence probabilites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can start by looking for cluster of pairwise dependence probabilities, or the chance that two columns depend on one another::

    ESTIMATE PAIRWISE DEPENDENCE PROBABILITY FROM satellites SAVE TO satellites_pairwise_dependence.png

.. image:: %s
:width: 1000px    

We can see there are a few distinct groups of variables:

Physical variables: class of orbit, apogee (farthest distance from earth while in orbit), perigee (shortest distance), and orbit period. We know that these variables must be related because of their physical relationships. Orbit class determines the distance and shape of the orbit, whose characteristics include apogee, perigee, and time to complete one orbit of earth (period).

Operators and contractors: contractor, country of contractor, and country of operator are also expected to be related, as countries and contractors are typically consistent partners in launching satellites.

Usage: purpose, expected_lifetime, and users. It seems reasonable to expect different purposes for different users, and for expected lifetime to be related. Some satellites will need to remain in service for a long time, while others may serve less demanding purposes.
""" % dependence_probability_figure_path

    satellites_fixture.comment(comment_0)

    orbit_perigee_figure_path = os.path.join(satellites_fixture.dir, 'satellites_orbit_perigee.png')
    out = satellites_fixture('PLOT SELECT class_of_orbit, perigee FROM <btable> SAVE TO ' + orbit_perigee_figure_path + ';')

    comment_1 = """
Let's visualize the relationship between class of orbit and perigee (closest distance to earth) - we should see pretty stark contrasts betwen low-earth orbit (LEO), medium-earth orbit (MEO), geosynchronous orbit (GEO, which means the satellite maintains position above a specific point on the earth's surface), and elliptical orbit, with elliptical having the broadest range, given the varying shapes possible.

.. image:: %s
:width: 1000px

The image shows exactly that: strong clustering of perigee values by orbit class.

""" % orbit_perigee_figure_path

    satellites_fixture.comment(comment_1)

    comment_2 = """
Unusual Satellites
^^^^^^^^^^^^^^^^^^

Which satellites show the least likelihood of their observed expected lifetimes? We know from basic physics that satellites in higher orbits generally remain in orbit for longer than those in lower orbits, due to the difference in atmospheric drag.

To confirm, we can review summary statistics of expected lifetime for satellites in low-earth orbit (LEO)::

    SUMMARIZE SELECT expected_lifetime FROM satellites WHERE class_of_orbit = "LEO"

And also for satellites in geosynchronous orbit::

    SUMMARIZE SELECT expected_lifetime from satellites WHERE class_of_orbit = "GEO"

"""

    satellites_fixture.comment(comment_2)

    out = satellites_fixture('SUMMARIZE SELECT expected_lifetime from <btable> WHERE class_of_orbit = "LEO";')
    mean_lifetime_leo = float(out[out[''] == 'mean']['expected_lifetime'])
    median_lifetime_leo = float(out[out[''] == '50%']['expected_lifetime'])
    assert mean_lifetime_leo < 7 and median_lifetime_leo < 7

    out = satellites_fixture('SUMMARIZE SELECT expected_lifetime from <btable> WHERE class_of_orbit = "GEO";')
    mean_lifetime_geo = float(out[out[''] == 'mean']['expected_lifetime'])
    median_lifetime_geo = float(out[out[''] == '50%']['expected_lifetime'])
    assert mean_lifetime_geo > 12 and median_lifetime_geo > 12

    comment_3 = """
We can see that the mean expected lifetime for a geosynchronous satellite is %5.2f years, with a median of %5.2f years, while for satellites in low-earth orbit, the same statistics are just %4.2f and %4.2f years, respectively. So which satellites does BayesDB identify as having unusual expected lifetimes, given their other characteristics?
""" % (mean_lifetime_geo, median_lifetime_geo, mean_lifetime_leo, median_lifetime_leo)

    satellites_fixture.comment(comment_3)

    out = satellites_fixture('SELECT country_of_operator, class_of_orbit, expected_lifetime FROM <btable> ORDER BY PREDICTIVE PROBABILITY OF expected_lifetime ASC LIMIT 10;')

    # Verify unusual LEO orbit lifetimes are much greater than the mean/median for LEO
    assert (out['expected_lifetime'][out['class_of_orbit'] == 'LEO'] > 2 * mean_lifetime_leo).all()
    assert (out['expected_lifetime'][out['class_of_orbit'] == 'LEO'] > 2 * median_lifetime_leo).all()
    # Verify unusual GEO orbit lifetimes are much less than the mean/median for GEO
    assert (out['expected_lifetime'][out['class_of_orbit'] == 'LEO'] > 0.5 * mean_lifetime_leo).all()
    assert (out['expected_lifetime'][out['class_of_orbit'] == 'LEO'] > 0.5 * median_lifetime_leo).all()

    comment_4 = """
The results show just what we might have expected: the satellites with the oddest expected lifetimes are those with long lifetimes in low-earth orbit, and short lifetimes in geosynchronous orbit.'

UCS was proactive about declaring that the expected lifetime variable is subject to change once satellites enter orbit. The [documentation](https://s3.amazonaws.com/ucs-documents/nuclear-weapons/sat-database/User-Guide-w-appendix-1-21-09.pdf) says "This figure can be misleading, especially in terms of scientific satellites. For example, the Akebono satellite, launched in 1989 with a design life of one year, is still functioning in 2009."
"""

    satellites_fixture.comment(comment_4)

    comment_5 = """
BayesDB as Fact Checker
^^^^^^^^^^^^^^^^^^^^^^^

While the section above highlights interesting differences in orbital periods, detecting such stark outliers may be a useful tool to uncover possible errors in the data set that could be harmful to inferences made in other analyses.

To test this, we can look for rows of data that don't fit deterministic relationships which we know should be true. As mentioned above, satellites in geosynchronous orbit stay positioned above specific points on the earth's surface, meaning their orbital period must equal the duration of one day on earth, or 1436 minutes (plus or minus a few for the unpredictabilites of space, like solar wind and varying gravitational pulls). So let's look at the satellites in geosynchronous orbit with the least probable orbital periods::

    SELECT class_of_orbit, period_minutes, PREDICTIVE PROBABILITY of period_minutes FROM satellites WHERE class_of_orbit = "GEO" ORDER BY PREDICTIVE PROBABILITY OF period_minutes ASC LIMIT 5

"""

    satellites_fixture.comment(comment_5)

    out = satellites_fixture('SELECT class_of_orbit, period_minutes, PREDICTIVE PROBABILITY of period_minutes FROM <btable> WHERE class_of_orbit = "GEO" ORDER BY PREDICTIVE PROBABILITY OF period_minutes ASC LIMIT 5;')
    # Focus on first four results:
    assert (out['class_of_orbit'][0:3] == 'GEO').all()
    assert (out['period_minutes'][0:3] < 1000).all()

    comment_6 = """
Four of the top five results are satellites where either class_of_orbit of period_minutes must be incorrect! This query pointed us directly to observations that need to be investigated and fixed.

What if we invert the direction of that analysis, and ask which satellites have the least likely orbital class for their orbital period?::

    SELECT class_of_orbit, period_minutes, PREDICTIVE PROBABILITY of class_of_orbit FROM satellites ORDER BY PREDICTIVE PROBABILITY OF class_of_orbit ASC LIMIT 5
"""

    satellites_fixture.comment(comment_6)

    out = satellites_fixture('SELECT class_of_orbit, period_minutes, PREDICTIVE PROBABILITY of class_of_orbit FROM <btable> ORDER BY PREDICTIVE PROBABILITY OF class_of_orbit ASC LIMIT 5;')
    n_elliptical = (out['class_of_orbit'] == 'Elliptical').sum()
    assert n_elliptical >= 3
    assert (out['period_minutes'] < 200).all()

    comment_7 = """
Interestingly, %d of the top 5 results have elliptical orbits with periods under 200 minutes. Let's check the distribution of orbit types for satellites with periods shorter than 200 minutes and see if elliptical orbits are indeed unusual::

    FREQ SELECT class_of_orbit FROM satellites WHERE period_minutes < 200

"""

    satellites_fixture.comment(comment_7)

    out = satellites_fixture('FREQ SELECT class_of_orbit FROM <btable> WHERE period_minutes < 200;')
    assert int(out['frequency'][out['class_of_orbit'] == 'Elliptical']) == 6
    proportion_elliptical = float(out['probability'][out['class_of_orbit'] == 'Elliptical'])
    assert proportion_elliptical < 0.01
    
    comment_8 = """
Indeed, of all the satellites in the database with a period less than 200 minutes, less than 1% have elliptical orbits. Rarity doesn't guarantee inaccuracy, of course, but again, it's certainly a pointer towards rows in the data set that should be checked thoroughly for accuracy and consistency.


Users and Expected Lifetimes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Wouldn't you want your investment in a satellite to last as long as possible? It seems only logical, but maybe there are different priorities for different users. Specifically, we might expect a commercial venture to want its satellites to last as long as possible, given the need to minimize launch costs and achieve a return on investment. If we simulate 100 users for satellites with an expected lifetime of 20 years::

    FREQ SIMULATE users FROM satellites TIMES 100 GIVEN expected_lifetime = 20

"""

    satellites_fixture.comment(comment_8)

    out = satellites_fixture('FREQ SIMULATE users FROM <btable> TIMES 100 GIVEN expected_lifetime = 20;')
    assert int(out['frequency'][out['users'] == 'Commercial']) >= 45

    comment_9 = """
We see that a majority of the simulated values are categorized as 'Commercial' users. Running the same query for satellites with expected lifetimes of only 5 years::

    FREQ SIMULATE users FROM satellites TIMES 100 GIVEN expected_lifetime = 5

"""

    satellites_fixture.comment(comment_9)

    out = satellites_fixture('FREQ SIMULATE users FROM <btable> TIMES 100 GIVEN expected_lifetime = 5;')
    assert int(out['frequency'][out['users'] == 'Commercial']) <= 40
    assert int(out['frequency'][out['users'] == 'Military']) <= 40
    assert int(out['frequency'][out['users'] == 'Government']) <= 40

    comment_10 = """
We see that many more of the simulated values are in the military/government categories.

Given that expected lifetime is so closely related to class_of_orbit (as we saw above), we'd expect to see a similar relationship for users and class of orbit. As a confirmatory step, let's try it out::

    FREQ SIMULATE users FROM satellites TIMES 100 GIVEN class_of_orbit = "GEO"

"""

    satellites_fixture.comment(comment_10)

    out = satellites_fixture('FREQ SIMULATE users FROM <btable> TIMES 100 GIVEN class_of_orbit = "GEO";')
    assert int(out['frequency'][out['users'] == 'Commercial']) >= 45

    comment_11 = """
Again we see that a majority of the simulated values for satellites in geosynchronous orbit (long expected lifetime) are categorized as 'Commercial' users. Running the same query for satellites with expected lifetimes of only 5 years::

    FREQ SIMULATE users FROM satellites TIMES 100 GIVEN class_of_orbit = "LEO"
"""

    satellites_fixture.comment(comment_11)

    out = satellites_fixture('FREQ SIMULATE users FROM <btable> TIMES 100 GIVEN class_of_orbit = "LEO";')
    assert int(out['frequency'][out['users'] == 'Commercial']) <= 40
    assert int(out['frequency'][out['users'] == 'Military']) <= 40
    assert int(out['frequency'][out['users'] == 'Government']) <= 40

    comment_12 = """
You can see many more government and military satellites in the simulated distribution for satellites in low-earth orbit, confirming that the same kind of relationship holds between users and class of orbit.


Smart Money?
^^^^^^^^^^^^

So are governments and militaries wasting money by only launching satellites with short lifetimes in close orbits? Or are they more constrained by launch budgets, or focusing on different services, like intelligence gathering or imaging of earth, where distance makes a difference?

Instead of simply listing the frequency of purpose by users, let's try clustering the satellites with respect to users and purpose, and see how those characteristics are split into groups.::

    ESTIMATE PAIRWISE ROW SIMILARITY WITH RESPECT TO users, purpose FROM satellites SAVE CLUSTERS WITH THRESHOLD 0.75 AS user_purpose_cluster SAVE TO user_purpose_cluster.png

Then we can check out the size of the detected clusters::

    SHOW ROW LISTS FOR satellites
"""

    satellites_fixture.comment(comment_12)

    out = satellites_fixture('ESTIMATE PAIRWISE ROW SIMILARITY WITH RESPECT TO users, purpose FROM <btable> SAVE CLUSTERS WITH THRESHOLD 0.75 AS user_purpose_cluster SAVE TO user_purpose_cluster.png;')
    out = satellites_fixture('SHOW ROW LISTS FOR <btable>;')

    # Verify two clusters > 400 rows in size
    assert (out['Row Count'] > 400).sum() == 2

    # Sort row counts, get list names of two largest
    row_counts = list(out['Row Count'])
    row_counts.sort()
    row_list_names = out['Row List Name'][out['Row Count'] >= row_counts[-2]]

    # Figure out which of the two clusters is commercial/communications, and which is gov/military/technology/reconnaissance
    row_list_communications = None
    row_list_gov_military = None

    for row_list_name in row_list_names:
        # Freq table of users and purpose for current list.
        out_freq_users = satellites_fixture('FREQ SELECT users FROM <btable> WHERE key in %s;' % row_list_name)
        out_freq_purpose = satellites_fixture('FREQ SELECT purpose FROM <btable> WHERE key in %s;' % row_list_name)

        users_commercial = str(out_freq_users['users'][0]) == 'Commercial' and out_freq_users['probability'][0] > 0.5
        purpose_communications = str(out_freq_purpose['purpose'][0]) == 'Communications' and float(out_freq_purpose['probability'][0]) > 0.75

        users_gov_military = str(out_freq_users['users'][0]) in ['Government', 'Military'] and float(out_freq_users['probability'][0]) > 0.2
        purpose_gov_military = str(out_freq_purpose['purpose'][1]) == 'Technology Development' and float(out_freq_purpose['probability'][1]) > 0.15

        if users_commercial and purpose_communications:
            row_list_communications = row_list_name
        elif users_gov_military and purpose_gov_military:
            row_list_gov_military = row_list_name


    # Check that both were assigned
    assert row_list_communications and row_list_gov_military

    comment_13 = """
Two very large clusters dominate the results, along with five more smaller groupings. Comparing the distributions of users and purpose in the first two clusters shows us that %s is mainly composed of satellites for commercial usage, for the purpose of communications, well-served by high-altitude satellites that can send signals to larger portions of earth:
::

    FREQ SELECT users FROM <btable> WHERE key in %s
    FREQ SELECT purpose FROM <btable> WHERE key in %s
""" % (row_list_communications, row_list_communications, row_list_communications)

    satellites_fixture.comment(comment_13)

    comment_14 = """
Meanwhile %s is more evenly spread between commercial, military, and government uses, with purposes also more evenly spread to things like remote sensing, earth observation, reconnaissance, earth science, and surveillance, all of which deliver better results from a closer distance to earth
::

    FREQ SELECT users FROM <btable> WHERE key in %s
    FREQ SELECT purpose FROM <btable> WHERE key in %s

Assuming that short lifetimes indicate wasteful investment is likely unfair, as it turns out - not only do military and government satellites serve different purposes that are better served by different orbits, but low-earth orbit is also cheaper to reach. [(source, see section 5.3)](http://www.iup.uni-bremen.de/~bms/remote_sensing/remote_sensing_chap5.pdf)

It's also worth noting there are plenty of satellites in the database where the users are categorized as 'Government/Commercial' or 'Military/Commercial', indicative of the level of cooperation between the private and public sectors in space technology. We focused on satellites listed as strictly one or the other to draw a sharper contrast.
""" % (row_list_gov_military, row_list_gov_military, row_list_gov_military)
    
    satellites_fixture.comment(comment_14)

    comment_15 = """
Notes and Caveats
-----------------

So maybe you know a little more about satellites now, right? We've learned a little bit about orbit classes and just how close and how far they take satellites from earth, information not very accessible to the backyard observer. We've also seen that some characteristics of satellites almost allow us to make definitive predictions about other characteristics (orbit class and perigee, orbit class and expected lifetime), and to strongly question observed values that don't match those predictions. In addition, we may have uncovered something about satellite expected lifetimes for different user groups.

Maybe it's worth downloading the data set and trying some queries yourself to see what you can find.

Once again, UCS deserves credit for aggregating and publishing the data, and they're more than welcoming to error reports - our demonstration of likely errors is intended to highlight BayesDB's ability to find improbable values, not to point a finger at their data collection efforts.

As noted in the documentation, the data collected comes from multiple sources, each with its own reporting methods and standards, so the results shown above should be considered preliminary and subject to further revisions as we refine our analysis.
"""

    satellites_fixture.comment(comment_15)

