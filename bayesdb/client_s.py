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


import json
import requests
import prettytable

import utils
import data_utils
import plotting_utils
import os

import pdb

default_args = dict(
        pretty=True,    # pretty print tables 
        timing=False, 
        wait=False,
        plots=None, 
        yes=True, 
        debug=False, 
        pandas_df=None, 
        pandas_output=True, 
        key_column=0)   # make sure that a new column for ID's are set by default

class Client_S(object):
    def __init__(self, bayesdb_host='127.0.0.1', bayesdb_port=8008 ):
        """
        Create a client_S object. Assumes an open server is running on localhost:8008.
        """
        self.hostname = bayesdb_host
        self.port = bayesdb_port
        self.URI = 'http://' + self.hostname + ':%d' % self.port
        self.call_id = 0
        print("NOTES:")
        print("-Currently does not support interactive queries, thus all y/n prompts will be "\
            "ignored. *Do not press return unless you mean it.*")
        print("-The client will not notify you when asynchronous ANALYZE commands have completed.")

    def execute(self, bql_string, **kwargs):
        self.call_id += 1

        # construct arguments using defaults
        params = default_args
        params['call_input'] = bql_string
        for key, item in kwargs.iteritems():
            params[key] = item

        # get something for the user
        params['return_raw_result'] = True

        # ignore interactive queries
        # params['yes'] = True
        # params['pretty'] = False # so that we get output
        # params['pandas_output'] = False # cannot pass pandas object
        message = {
            'jsonrpc': '2.0',
            'method': 'execute',
            'params': params,
            'id': str(self.call_id),
            }
        json_message = json.dumps(message)

        self.call_id 
        r = requests.put(self.URI, data=json_message)
        r.raise_for_status()
        out = json.loads(r.content)

        if isinstance(out, dict) and 'result' in out:
            if isinstance(out['result'][0], str) or isinstance(out['result'][0], unicode):
                print( "ERROR: %s" % (out['result'][0]) )
                return None

            result = out['result'][0]['result']
            method_name = out['result'][0]['method_name']
            client_dict = out['result'][0]['client_dict']
        else:
            print "call(client.execute, <%s>, %s): ERROR" % (params, self.URI)
            return None
        
        assert type(result) != int

        plots = params['plots']
        pretty = params['pretty']
        pandas_output = params['pandas_output']
        pandas_df = params['pandas_df']

        if plots is None:
            plots = 'DISPLAY' in os.environ.keys()

        if 'matrix' in result and (plots or client_dict['filename']):
            # Plot matrices
            plotting_utils.plot_matrix(result['matrix'], result['column_names'], result['title'], client_dict['filename'])
            if pretty:
                if 'column_lists' in result:
                    print self.pretty_print(dict(column_lists=result['column_lists']))
                return self.pretty_print(result)
            else:
                return result
        if ('plot' in client_dict and client_dict['plot']):
            if (plots or client_dict['filename']):
                # Plot generalized histograms or scatterplots
                plot_remove_key = method_name in ['select', 'infer']
                plotting_utils.plot_general_histogram(result['columns'], result['data'], result['M_c'], client_dict['filename'], client_dict['scatter'], remove_key=plot_remove_key)
                return self.pretty_print(result)
            else:
                if 'message' not in result:
                    result['message'] = ""
                result['message'] = "Your query indicates that you would like to make a plot, but in order to do so, you must either enable plotting in a window or specify a filename to save to by appending 'SAVE TO <filename>' to this command.\n" + result['message']

        if pretty:
            pp = self.pretty_print(result)
            print pp

        # Print warnings last so they're readable without scrolling backwards.
        if 'warnings' in result:
            """ Pretty-print warnings. """
            for warning in result['warnings']:
                print 'WARNING: %s' % warning
                
        if pandas_output and 'data' in result and 'columns' in result:
            result_pandas_df = data_utils.construct_pandas_df(result)
            return result_pandas_df
        else:
            return result

    def __call__(self, bql_string, **kwargs):
        """Wrapper around execute."""
        # pretty=True, timing=False, wait=False, plots=None, yes=False, debug=False, pandas_df=None, pandas_output=True, key_column=None
        return self.execute(bql_string, **kwargs)


    def pretty_print(self, query_obj):
        """
        Return a pretty string representing the output object.
        """
        assert type(query_obj) == dict
        result = ""
        if type(query_obj) == dict and 'message' in query_obj:
            result += query_obj["message"] + "\n"
        if 'data' in query_obj and 'columns' in query_obj:
            """ Pretty-print data table """
            pt = prettytable.PrettyTable()
            pt.field_names = query_obj['columns']
            for row in query_obj['data']:
                pt.add_row(row)
            result += str(pt)
        elif 'list' in query_obj:
            """ Pretty-print lists """
            result += str(query_obj['list'])
        elif 'column_names' in query_obj:
            """ Pretty-print cctypes """
            colnames = query_obj['column_names']
            zmatrix = query_obj['matrix']
            pt = prettytable.PrettyTable(hrules=prettytable.ALL, vrules=prettytable.ALL, header=False)
            pt.add_row([''] + list(colnames))
            for row, colname in zip(zmatrix, list(colnames)):
                pt.add_row([colname] + list(row))
            result += str(pt)
        elif 'columns' in query_obj:
            """ Pretty-print column list."""
            pt = prettytable.PrettyTable()
            pt.field_names = ['column']
            for column in query_obj['columns']:
                pt.add_row([column])
            result += str(pt)
        elif 'row_lists' in query_obj:
            """ Pretty-print multiple row lists, which are just names and row sizes. """
            pt = prettytable.PrettyTable()
            pt.field_names = ('Row List Name', 'Row Count')
            
            def get_row_list_sorting_key(x):
                """ To be used as the key function in a sort. Puts cc_2 ahead of cc_10, e.g. """
                name, count = x
                if '_' not in name:
                    return name
                s = name.split('_')
                end = s[-1]
                start = '_'.join(s[:-1])
                if utils.is_int(end):
                    return (start, int(end))
                return name
                    
            for name, count in sorted(query_obj['row_lists'], key=get_row_list_sorting_key):
                pt.add_row((name, count))
            result += str(pt)
        elif 'column_lists' in query_obj:
            """ Pretty-print multiple column lists. """
            print
            clists = query_obj['column_lists']
            for name, clist in clists:
                print "%s:" % name
                pt = prettytable.PrettyTable()
                pt.field_names = clist
                print pt
        elif 'models' in query_obj:
            """ Pretty-print model info. """
            pt = prettytable.PrettyTable()
            pt.field_names = ('model_id', 'iterations')
            for (id, iterations) in query_obj['models']:
                pt.add_row((id, iterations))
            result += str(pt)

        if len(result) >= 1 and result[-1] == '\n':
            result = result[:-1]
        return result
 



