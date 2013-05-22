#
# Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import os
import inspect
#
import tabular_predDB.python_utils.general_utils as gu
import tabular_predDB.python_utils.xnet_utils as xu

hadoop_home = os.environ.get('HADOOP_HOME', '')
#
default_which_hadoop_binary = os.path.join(hadoop_home, 'bin/hadoop')
default_which_hadoop_jar = "/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.1.2.jar"
default_which_engine_binary = "hadoop_line_processor"
default_hdfs_uri = "hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/"
default_jobtracker_uri = "xd-jobtracker.xdata.data-tactics-corp.com:8021"
default_hdfs_dir = "/user/bigdata/SSCI/test_remote_streaming/"
#
input_filename = 'hadoop_input'
table_data_filename = xu.default_table_data_filename
output_path = 'myOutputDir'


DEBUG = False

class HadoopEngine(object):

    # FIXME: where is binary created/sent?
    def __init__(self, seed=0,
                 which_engine_binary=default_which_engine_binary,
                 hdfs_dir=default_hdfs_dir,
                 jobtracker_uri=default_jobtracker_uri,
                 hdfs_uri=default_hdfs_uri,
                 which_hadoop_jar=default_which_hadoop_jar,
                 ):
        assert_vpn_is_connected()
        #
        self.which_hadoop_binary = default_which_hadoop_binary
        #
        self.seed_generator = gu.int_generator(seed)
        self.which_engine_binary = which_engine_binary
        self.hdfs_dir = hdfs_dir
        self.jobtracker_uri = jobtracker_uri
        self.hdfs_uri = hdfs_uri
        self.which_hadoop_jar = which_hadoop_jar
        return

    def initialize(self, M_c, M_r, T, initialization='from_the_prior',
                   n_chains=1):
        assert_vpn_is_connected()
        initialize_args_dict = dict(command='initialize', initialization=initialization)
        #
        table_data = dict(M_c=M_c, M_r=M_r, T=T)
        xu.pickle_table_data(table_data, table_data_filename)
        xu.write_initialization_files(input_filename, initialize_args_dict, n_chains)
        os.system('cp %s initialize_input' % input_filename)
        was_successful = send_hadoop_command(self,
                                            table_data_filename,
                                            input_filename, output_path,
                                            n_tasks=n_chains)
        hadoop_output = None
        if was_successful:
            hadoop_output = read_hadoop_output(output_path)
            hadoop_output_filename = get_hadoop_output_filename(output_path)
            os.system('cp %s initialize_output' % hadoop_output_filename)
        return hadoop_output

    def analyze(self, M_c, T, X_L, X_D, kernel_list=(), n_steps=1, c=(), r=(),
                max_iterations=-1, max_time=-1):
        assert_vpn_is_connected()
        analyze_args_dict = dict(command='analyze', kernel_list=kernel_list, n_steps=n_steps, c=c, r=r)
        if not xu.get_is_multistate(X_L, X_D):
            X_L = [X_L]
            X_D = [X_D]
        #
        table_data = dict(M_c=M_c, M_r=M_r, T=T)
        xu.pickle_table_data(table_data, table_data_filename)
        with open(input_filename, 'w') as fh:
            for SEED, (X_L_i, X_D_i) in enumerate(zip(X_L, X_D)):
                dict_out = dict(X_L=X_L_i, X_D=X_D_i, SEED=SEED)
                dict_out.update(analyze_args_dict)
                xu.write_hadoop_line(fh, SEED, dict_out)
        os.system('cp %s analyze_input' % input_filename)
        was_successful = send_hadoop_command(self,
                                            table_data_filename,
                                            input_filename, output_path,
                                            n_tasks=len(X_L))
        hadoop_output = None
        if was_successful:
            hadoop_output = read_hadoop_output(output_path)
            hadoop_output_filename = get_hadoop_output_filename(output_path)
            os.system('cp %s analyze_output' % hadoop_output_filename)
        return hadoop_output

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, Q, n=1):
        pass

    def impute(self, M_c, X_L, X_D, Y, Q, n):
        pass

    def impute_and_confidence(self, M_c, X_L, X_D, Y, Q, n):
        pass

def get_is_vpn_connected():
    cmd_str = 'ifconfig | grep tun'
    lines = [line for line in os.popen(cmd_str)]
    is_vpn_connected = False
    if len(lines) != 0:
        is_vpn_connected = True
    return is_vpn_connected

def assert_vpn_is_connected():
    is_vpn_connected = get_is_vpn_connected()
    assert is_vpn_connected
    return

def rm_hdfs(hdfs_uri, path, hdfs_base_dir=''):
    hdfs_path = os.path.join(hdfs_base_dir, path)
    cmd_str = 'hadoop fs -fs "%s" -rm -r -f %s'
    cmd_str %= (hdfs_uri, hdfs_path)
    if DEBUG:
        print cmd_str
    else:
        os.system(cmd_str)
    return

def rm_local(path):
    cmd_str = 'rm -rf %s'
    cmd_str %= path
    if DEBUG:
        print cmd_str
    else:
        os.system(cmd_str)
    return

def get_hdfs(hdfs_uri, path, hdfs_base_dir=''):
    hdfs_path = os.path.join(hdfs_base_dir, path)
    # clear local path
    rm_local(path)
    # get from hdfs
    cmd_str = 'hadoop fs -fs "%s" -get %s %s'
    cmd_str %= (hdfs_uri, hdfs_path, path)
    if DEBUG:
        print cmd_str
    else:
        os.system(cmd_str)
    return

def put_hdfs(hdfs_uri, path, hdfs_base_dir=''):
    hdfs_path = os.path.join(hdfs_base_dir, path)
    # clear hdfs path
    rm_hdfs(hdfs_uri, path, hdfs_base_dir)
    # put to hdfs
    cmd_str = 'hadoop fs -fs "%s" -put %s %s'
    cmd_str %= (hdfs_uri, path, hdfs_path)
    if DEBUG:
        print cmd_str
    else:
        os.system(cmd_str)
    return

def create_hadoop_cmd_str(hadoop_engine, task_timeout=600000, n_tasks=1):
    hdfs_path = hadoop_engine.hdfs_uri + hadoop_engine.hdfs_dir
    archive_path = os.path.join(hdfs_path, 
                                hadoop_engine.which_engine_binary + '.jar')
    ld_library_path = os.environ.get('LD_LIBRARY_PATH', '')
    ld_library_path = './%s.jar:%s' % (hadoop_engine.which_engine_binary,
                                       ld_library_path)
    mapper_path = '%s.jar/%s' % (hadoop_engine.which_engine_binary,
                                 hadoop_engine.which_engine_binary)
    #
    jar_str = '%s jar %s' % (hadoop_engine.which_hadoop_binary,
                             hadoop_engine.which_hadoop_jar)
    archive_str = '-archives "%s"' % archive_path
    cmd_env_str = '-cmdenv LD_LIBRARY_PATH=%s' % ld_library_path
    hadoop_cmd_str = ' '.join([
            jar_str,
            '-D mapred.task.timeout=%s' % task_timeout,
            '-D mapred.map.tasks=%s' % n_tasks,
            archive_str,
            '-fs "%s"' % hadoop_engine.hdfs_uri,
            '-jt "%s"' % hadoop_engine.jobtracker_uri,
            '-input "%s"' % os.path.join(hdfs_path, input_filename),
            '-output "%s"' % os.path.join(hdfs_path, output_path),
            '-mapper "%s"' % mapper_path,
            '-reducer /bin/cat',
            '-file %s' % input_filename,
            '-file %s' % table_data_filename,
            cmd_env_str,
            ])
    return hadoop_cmd_str

def get_was_successful(output_path):
    success_file = os.path.join(output_path, '_SUCCESS')
    was_successful = os.path.isfile(success_file)
    return was_successful

def send_hadoop_command(hadoop_engine, table_data_filename, input_filename,
                        output_path, n_tasks):
    # set up files
    put_hdfs(hadoop_engine.hdfs_uri, input_filename, hdfs_base_dir=hadoop_engine.hdfs_dir)
    put_hdfs(hadoop_engine.hdfs_uri, table_data_filename,
             hdfs_base_dir=hadoop_engine.hdfs_dir)
    rm_hdfs(hadoop_engine.hdfs_uri, output_path, hdfs_base_dir=hadoop_engine.hdfs_dir)
    # actually send
    hadoop_cmd_str = create_hadoop_cmd_str(hadoop_engine, n_tasks=n_tasks)
    if DEBUG:
        print hadoop_cmd_str
    else:
        os.system(hadoop_cmd_str + ' >out 2>err')
    # retrieve resutls
    get_hdfs(hadoop_engine.hdfs_uri, output_path, hdfs_base_dir=hadoop_engine.hdfs_dir)
    #
    was_successful = get_was_successful(output_path)
    return was_successful

def write_hadoop_input():
    pass

def get_hadoop_output_filename(output_path):
    hadoop_output_filename = os.path.join(output_path, 'part-00000')
    return hadoop_output_filename
def read_hadoop_output(output_path):
    hadoop_output_filename = get_hadoop_output_filename(output_path)
    with open(hadoop_output_filename) as fh:
        ret_dict = dict([xu.parse_hadoop_line(line) for line in fh])
    return ret_dict

if __name__ == '__main__':
    import tabular_predDB.python_utils.data_utils as du
    T, M_r, M_c = du.read_model_data_from_csv('../www/data/dha_small.csv', gen_seed=0)
    #
    he = HadoopEngine()
    hadoop_output = he.initialize(M_c, M_r, T, initialization='from_the_prior',
                                  n_chains=4)
    X_L_list = [el['X_L'] for el in hadoop_output.values()]
    X_D_list = [el['X_D'] for el in hadoop_output.values()]
    hadoop_output = he.analyze(M_c, T, X_L_list, X_D_list)
