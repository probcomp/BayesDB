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
    try:
        assert(a >= b*(1.0+tol))
    except AssertionError, e:
        raise AssertionError("a(%s) is not %f greater than b(%s)." % (str(a), tol*100, str(b)))


def assertLessThan(a, b, tol=0):
    try:
        assert(a < b*(1.0-tol))
    except AssertionError, e:
        raise AssertionError("a(%s) is not %f less than than b(%s)." % (str(a), tol*100, str(b)))


def assertClose(a, b, tol=10E-6):
    try:
        assert(abs(a-b) < tol)
    except AssertionError:
        raise AssertionError("Differente (%f) between a(%f) and b(%f) if greate than %f."
                             % (abs(a-b), a, b, tol))


def assertIn(a, b):
    assert(a in b)


def assertNotIn(a, b):
    assert(a not in b)


class TestClient(Client):
    """docstring for TestClient"""
    def __init__(self, test_id, csv_filename, model_filename=None, num_models=10,
                 num_analyze_iterations=250, num_analyze_minutes=None, schema_update_commands=[],
                 key_column=0):

        super(TestClient, self).__init__()
        self.test_id = test_id
        self.csv_filename = csv_filename
        self.commands = []
        self.comments = []
        self.commment_indices = []
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
                                            key_column=key_column, debug=False, yes=True)

            # restore normal output output
            sys.stdout = oldstdout
            self.output.append(out.getvalue())

    def finalize(self):
        """ Saves the models, drops the btable and (TODO) generates .rst output
        """
        output_model_filename = self.btable_name + '_models.pkl.gz'
        super(TestClient, self).execute('SAVE MODELS FROM %s TO %s;'
                                        % (self.btable_name, output_model_filename), yes=True)
        super(TestClient, self).execute('DROP BTABLE %s;' % (self.btable_name), yes=True)
        output = {
            'test_id': self.test_id,
            'commands': self.commands,
            'comments': self.comments,
            'commment_indices': self.commment_indices,
            'output': self.output,
            'output_model_filename': output_model_filename,
            'timestamp': self.timestamp
        }
        print(self.commands)
        # TODO: save sphinx output if needed
        pickle.dump(output, open(os.path.join(self.dir, 'output.pkl'), 'wb'))

    def comment(self, comment_text):
        """ Add a comment after current command
        """
        self.comments.append(comment_text)
        self.commment_indices.append(len(self.commands))

    def __call__(self, call_input, pretty=False, timing=False, wait=False, plots=None, yes=False,
                 debug=False, pandas_df=True, pandas_output=True, key_column=None,
                 return_raw_result=False, ignore_output=False):
        """ Calls BayesDB Client, redirects and saves output, and outputs data.
        """
        # # redirect print output
        # out = StringIO.StringIO()
        # oldstdout = sys.stdout
        # sys.stdout = out

        res = super(TestClient, self).execute(call_input.replace('<btable>', self.btable_name),
                                              pretty, timing, wait, plots, yes, debug, pandas_df,
                                              pandas_output, key_column, return_raw_result)
        # # restore normal output output
        # sys.stdout = oldstdout
        # self.output.append(out.getvalue())

        if not ignore_output:
            self.commands.append(call_input)

        if res is not None:
            return res[0]
        else:
            return None
