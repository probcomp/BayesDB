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

from bayesdb.client import Client
import StringIO  # for python 3, replace with io
import os
import sys
import time
import pickle


def assertGreaterThan(a, b, tol=0):
    """ Assert that a is at least tol greater than b.

    Examples: 
        >>> assertGreaterThan(7, 5, tol=0)  # passes
        >>> assertGreaterThan(7, 5, tol=1)  # passes
        >>> assertGreaterThan(7, 5, tol=5)  # fails
    """
    try:
        assert(a >= b*(1.0+tol))
    except AssertionError:
        raise AssertionError("a(%s) is not %f greater than b(%s)." % (str(a), tol*100, str(b)))


def assertLessThan(a, b, tol=0):
    """ Assert that a is at least tol less than b.

    Examples:
        >>> assertLessThan(5, 7, tol=0)  # passes
        >>> assertLessThan(5, 7, tol=1)  # passes
        >>> assertLessThan(5, 7, tol=5)  # fails
    """
    try:
        assert(a < b*(1.0-tol))
    except AssertionError:
        raise AssertionError("a(%s) is not %f less than than b(%s)." % (str(a), tol*100, str(b)))


def assertClose(a, b, tol=10E-6):
    """ Asset that a is within tol of b.

    Examples:
        >>> assertClose(2.0, 2.1, tol=.2)  # passes
        >>> assertClose(2.1, 2.0, tol=.2)  # passes
        >>> assertClose(2.0, 2.1)  # fails
    """
    try:
        assert(abs(a-b) < tol)
    except AssertionError:
        raise AssertionError("Difference (%f) between a(%f) and b(%f) if greate than %f."
                             % (abs(a-b), a, b, tol))


def assertIn(a, b):
    assert(a in b)


def assertNotIn(a, b):
    assert(a not in b)


class TestClient(Client):
    """ 
    Wrapper for Client. Test fixture for appyling unit tests to use cases and generating 
    sphinx-ready docs.

    Attributes:
        test_id (str): Name of test. Used to name files. Replaces instances pf 'btable' in sphinx 
            output.
        csv_filename (string): Name of csv datafile for btable creation
        commands (list of str): List of commands executed during btable creation as well as those 
            executed by the user.
        comments (list of str): List of comments (in .rst format) added by the user.
        comment_indices (list of int): Stores the command index of the comment. That is, 
            comment_indices[i] = j means that comments[i] should be placed before immediately 
            before command j.
        output (list of str): Stores resulting pretty output of each command.
        timestamp (str): ID used for file naming.
        btable_name (str): Name of btable used for test.
        dir (str): Name of the directory to which files are saved.

    Notes:
        See tests/example_tests/test_dha_example.py for a detailed use example.

    """
    def __init__(self, test_id, csv_filename, model_filename=None, num_models=10,
                 num_analyze_iterations=250, num_analyze_minutes=None, schema_update_commands=[],
                 key_column=0):
        """
        Create TestClient object, CREATE, INITIALIZE, ANALYZE, and (optionally) UPDATE btable, and
        fill in initial commands and output.

        Args:
            test_id (str): Name of test. Used to name files. Replaces instances pf 'btable' in sphinx 
                output.
            csv_filename (string): Name of csv datafile for btable creation

        Kwargs:
            model_filename (str): Filename of models to load. If None (default) creates and 
                analyzes new models.
            num_models (int): Number of models to create for btable.
            num_analyze_iterations (int): Number of iterations to analyze btable.
            num_analyze_minutes (int): Number of minutes to analyze btable. If not None (default), 
                overrides num_analyze_iterations.
            schema_update_commands (list of str): List of commands to run after initialization. Use
                these commands to update schema or add codebooks on start up.
            key_column (int): Key column of btable.

        Example:
            Create Tester object, analyze 100 models and update schema.
            >>> cmds = ['UPDATE SCHEMA FOR <btable> SET nbrhd=categorical']
            >>> tclient = TestClient('homes','data/homes.csv', num_models=100, schema_update_commands=cmds)
        """

        super(TestClient, self).__init__()
        self.test_id = test_id
        self.csv_filename = csv_filename
        self.commands = []
        self.comments = []
        self.comment_indices = []
        self.output = []

        # create timestamp and temp directory
        self.timestamp = '_' + str(int(time.time()*100))
        self.btable_name = test_id + self.timestamp

        self.dir = os.path.join('data', test_id, test_id+self.timestamp)
        # create datat directory
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        self._initialize(model_filename, num_models, num_analyze_iterations, num_analyze_minutes,
                         schema_update_commands, key_column)
        # create btable

    def _initialize(self, model_filename=None, num_models=10, num_analyze_iterations=250,
                    num_analyze_minutes=None, schema_update_commands=[], key_column=0):
        commands = []
        create_btable_cmd = 'CREATE BTABLE <btable> FROM %s;' % (self.csv_filename)
        commands.append(create_btable_cmd)
        if model_filename is not None:
            load_model_cmd = 'LOAD MODELS %s INTO <btable>;' % (model_filename)
            commands.append(load_model_cmd)
        else:
            init_models_cmd = 'INITIALIZE %i MODELS FOR <btable>;' % (num_models)
            commands.append(init_models_cmd)
            commands.extend(schema_update_commands)
            if num_analyze_minutes is not None:
                analyze_cmd = 'ANALYZE <btable> FOR %i MINUTES WAIT;' % (num_analyze_minutes)
            else:
                analyze_cmd = 'ANALYZE <btable> FOR %i ITERATIONS WAIT;' % (num_analyze_iterations)
            commands.append(analyze_cmd)

        self.commands = commands

        for cmd in commands:
            # redirect print output
            out = StringIO.StringIO()
            oldstdout = sys.stdout
            sys.stdout = out

            super(TestClient, self).execute(cmd.replace('<btable>', self.btable_name), pretty=True,
                                            key_column=key_column, debug=False, yes=True,
                                            force_output=True)

            # restore normal output output
            sys.stdout = oldstdout
            self.output.append(out.getvalue())

    def finalize(self):
        """ Saves the models, drops the btable and (TODO) generates .rst output
        """
        output_model_filename = os.path.join(self.dir, self.btable_name + '_models.pkl.gz')
        super(TestClient, self).execute('SAVE MODELS FROM %s TO %s;'
                                        % (self.btable_name, output_model_filename), yes=True)
        super(TestClient, self).execute('DROP BTABLE %s;' % (self.btable_name), yes=True)
        output = {
            'test_id': self.test_id,
            'commands': self.commands,
            'comments': self.comments,
            'comment_indices': self.comment_indices,
            'output': self.output,
            'output_model_filename': output_model_filename,
            'timestamp': self.timestamp
        }

        # save sphinx output if needed
        self.build_rst()
        pickle.dump(output, open(os.path.join(self.dir, 'output.pkl'), 'wb'))

    def build_rst(self):
        """ Build .rst file and save to dir
        """
        txt_idx = 0
        cmd_idx = 0
        rst_output = ""

        while txt_idx < len(self.comments) and cmd_idx < len(self.commands):
            while self.comment_indices[txt_idx] <= cmd_idx:
                rst_output += self.comments[txt_idx].rstrip()
                txt_idx += 1
                if self.comment_indices[txt_idx] <= cmd_idx:
                    rst_output += '\n'

            rst_output += "::\n\n"

            next_cmt_idx = self.comment_indices[txt_idx]
            while cmd_idx < next_cmt_idx:
                cmd_txt = '\t>>> ' + self.commands[cmd_idx] + '\n' + '\t'
                out_text = self.output[cmd_idx].replace('\n', '\n\t').replace(self.btable_name, self.test_id) + '\n'
                rst_output += cmd_txt.replace(self.dir+'/', '') + out_text
                cmd_idx += 1

            rst_output += "\n"

        if txt_idx < len(self.comments):
            for comment in self.comments[txt_idx:]:
                rst_output += comment + '\n'

        rst_output = rst_output.replace('<btable>', self.test_id)

        with open(os.path.join(self.dir, 'output.rst'), 'wb') as f:
            f.write(rst_output)

    def comment(self, comment_text, introduction=False):
        """ Add a comment after current command

        Args:
            comment_text (str): .rst-formatted text to add. Comments are added in the order in 
                which they are supplied.

        Kwargs:
            introduction (bool): If true, adds the comment before the btable initialization 
                commands. Note that the introduction comment must be added first.
        """
        if introduction:
            if len(self.comments) > 0:
                raise ValueError("Introduction must be first comment added.")
            self.comment_indices.append(0)
        else:
            self.comment_indices.append(len(self.commands))

        self.comments.append(comment_text)

    def __call__(self, call_input, pretty=True, timing=False, wait=False, plots=None, yes=False,
                 debug=False, pandas_df=True, pandas_output=True, key_column=None,
                 return_raw_result=False, ignore_output=False, force_output=True):
        """ Calls BayesDB Client, redirects and saves output, and returns data.
        """
        # redirect print output
        out = StringIO.StringIO()
        oldstdout = sys.stdout
        sys.stdout = out

        res = super(TestClient, self).execute(call_input.replace('<btable>', self.btable_name),
                                              pretty, timing, wait, plots, yes, debug, pandas_df,
                                              pandas_output, key_column, return_raw_result,
                                              force_output)
        # restore normal output output
        sys.stdout = oldstdout
        self.output.append(out.getvalue())

        if not ignore_output:
            self.commands.append(call_input)

        if res is not None:
            return res[0]
        else:
            return None
