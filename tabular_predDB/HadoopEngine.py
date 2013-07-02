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
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.general_utils as gu
import tabular_predDB.python_utils.xnet_utils as xu


DEFAULT_CLUSTER = 'xdata_highmem'
DEBUG = False

xdata_hadoop_jar_420 = "/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.2.0.jar"
xdata_hadoop_jar_412 = "/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.1.2.jar"

default_xdata_hadoop_jar = xdata_hadoop_jar_420 if os.path.exists(xdata_hadoop_jar_420) else xdata_hadoop_jar_412
default_xdata_compute_hdfs_uri = "hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/"
default_xdata_compute_jobtracker_uri = "xd-jobtracker.xdata.data-tactics-corp.com:8021"
default_xdata_highmem_hdfs_uri = "hdfs://xd-hm-nn.xdata.data-tactics-corp.com:8020/"
default_xdata_highmem_jobtracker_uri = "xd-hm-jt.xdata.data-tactics-corp.com:8021"
#
default_starcluster_hadoop_jar = "/usr/lib/hadoop-0.20/contrib/streaming/hadoop-streaming-0.20.2-cdh3u2.jar"
default_starcluster_hdfs_uri = None
default_starcluster_jobtracker_uri = None
#
if DEFAULT_CLUSTER == 'starcluster':
  default_hadoop_jar = default_starcluster_hadoop_jar
  default_hdfs_uri = default_starcluster_hdfs_uri
  default_jobtracker_uri = default_starcluster_jobtracker_uri
else:
  default_hadoop_jar = default_xdata_hadoop_jar
  if DEFAULT_CLUSTER == 'xdata_compute':
    default_hdfs_uri = default_xdata_compute_hdfs_uri
    default_jobtracker_uri = default_xdata_compute_jobtracker_uri
  else:
    default_hdfs_uri = default_xdata_highmem_hdfs_uri
    default_jobtracker_uri = default_xdata_highmem_jobtracker_uri
#
default_hadoop_binary = 'hadoop'
default_engine_binary = "/user/bigdata/SSCI/hadoop_line_processor"
default_hdfs_dir = "/user/bigdata/SSCI/"
default_output_path = 'myOutputDir'
default_input_filename = 'hadoop_input'
default_table_data_filename = xu.default_table_data_filename


class HadoopEngine(object):

    # FIXME: where is binary created/sent?
    def __init__(self, seed=0,
                 which_engine_binary=default_engine_binary,
                 hdfs_dir=default_hdfs_dir,
                 jobtracker_uri=default_jobtracker_uri,
                 hdfs_uri=default_hdfs_uri,
                 which_hadoop_jar=default_hadoop_jar,
		 which_hadoop_binary=default_hadoop_binary,
                 output_path=default_output_path,
                 input_filename=default_input_filename,
                 table_data_filename=default_table_data_filename,
                 ):
        xu.assert_vpn_is_connected()
        #
        self.which_hadoop_binary = which_hadoop_binary
        #
        self.seed_generator = gu.int_generator(seed)
        self.which_engine_binary = which_engine_binary
        self.hdfs_dir = hdfs_dir
        self.jobtracker_uri = jobtracker_uri
        self.hdfs_uri = hdfs_uri
        self.which_hadoop_jar = which_hadoop_jar
        self.output_path = output_path
        self.input_filename = input_filename
        self.table_data_filename = table_data_filename
        return

    def initialize(self, M_c, M_r, T, initialization='from_the_prior',
                   n_chains=1):
      output_path = self.output_path
      input_filename = self.input_filename
      table_data_filename = self.table_data_filename
      xu.assert_vpn_is_connected()
      #
      initialize_args_dict = dict(command='initialize', initialization=initialization)
      #
      table_data = dict(M_c=M_c, M_r=M_r, T=T)
      xu.pickle_table_data(table_data, table_data_filename)
      # fixme: need to prepend output_path to input_filename
      xu.write_initialization_files(input_filename, initialize_args_dict, n_chains)
      # os.system('cp %s initialize_input' % input_filename)
      was_successful = send_hadoop_command(self,
                                           table_data_filename,
                                           input_filename, output_path,
                                           n_tasks=n_chains)
      hadoop_output = None
      if was_successful:
        hadoop_output = read_hadoop_output(output_path)
        hadoop_output_filename = get_hadoop_output_filename(output_path)
        os.system('cp %s initialize_output' % hadoop_output_filename)
        X_L_list = [el['X_L'] for el in hadoop_output.values()]
        X_D_list = [el['X_D'] for el in hadoop_output.values()]
        # make output format match LocalEngine
        hadoop_output = M_c, M_r, X_L_list, X_D_list
      return hadoop_output

    def analyze(self, M_c, T, X_L, X_D, kernel_list=(), n_steps=1, c=(), r=(),
                max_iterations=-1, max_time=-1):
        output_path = self.output_path
        input_filename = self.input_filename
        table_data_filename = self.table_data_filename
        xu.assert_vpn_is_connected()
        #
        analyze_args_dict = dict(command='analyze', kernel_list=kernel_list,
                                 n_steps=n_steps, c=c, r=r)
        if not xu.get_is_multistate(X_L, X_D):
            X_L = [X_L]
            X_D = [X_D]
        #
        table_data = dict(M_c=M_c, T=T)
        # fixme: need to prepend output_path to table_data_filename
        xu.pickle_table_data(table_data, table_data_filename)
        # fixme: need to prepend output_path to input_filename
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
            X_L_list = [el['X_L'] for el in hadoop_output.values()]
            X_D_list = [el['X_D'] for el in hadoop_output.values()]
            # make output format match LocalEngine
            hadoop_output = X_L_list, X_D_list
        return hadoop_output

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, Q, n=1):
        pass

    def impute(self, M_c, X_L, X_D, Y, Q, n):
        pass

    def impute_and_confidence(self, M_c, X_L, X_D, Y, Q, n):
        pass

def rm_hdfs(hdfs_uri, path, hdfs_base_dir=''):
    rm_infix_args = '-rmr'
    # rm_infix_args = '-rm -r -f'
    hdfs_path = os.path.join(hdfs_base_dir, path)
    fs_str = ('-fs "%s"' % hdfs_uri) if hdfs_uri is not None else ''
    cmd_str = 'hadoop fs %s %s %s'
    cmd_str %= (fs_str, rm_infix_args, hdfs_path)
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
    fs_str = ('-fs "%s"' % hdfs_uri) if hdfs_uri is not None else ''
    cmd_str = 'hadoop fs %s -get %s %s'
    cmd_str %= (fs_str, hdfs_path, path)
    if DEBUG:
        print cmd_str
    else:
        os.system(cmd_str)
    return

def ensure_dir_hdfs(fs_str, hdfs_path):
  dirname = os.path.split(hdfs_path)[0]
  cmd_str = 'hadoop fs %s -mkdir %s'
  cmd_str %= (fs_str, dirname)
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
    fs_str = ('-fs "%s"' % hdfs_uri) if hdfs_uri is not None else ''
    ensure_dir_hdfs(fs_str, hdfs_path)
    cmd_str = 'hadoop fs %s -put %s %s'
    cmd_str %= (fs_str, path, hdfs_path)
    if DEBUG:
        print cmd_str
    else:
        os.system(cmd_str)
    return

def create_hadoop_cmd_str(hadoop_engine, task_timeout=60000000, n_tasks=1):
    hdfs_uri = hadoop_engine.hdfs_uri if hadoop_engine.hdfs_uri is not None else "hdfs://"
    hdfs_path = os.path.join(hdfs_uri, hadoop_engine.hdfs_dir)
    # note: hdfs_path is hadoop_engine.hdfs_dir is omitted
    archive_path = hdfs_uri + hadoop_engine.which_engine_binary + '.jar'
    engine_binary_infix = os.path.splitext(os.path.split(hadoop_engine.which_engine_binary)[-1])[0]
    ld_library_path = os.environ.get('LD_LIBRARY_PATH', '')
    ld_library_path = './%s.jar:%s' % (engine_binary_infix, ld_library_path)
    mapper_path = '%s.jar/%s' % (engine_binary_infix, engine_binary_infix)
    #
    jar_str = '%s jar %s' % (hadoop_engine.which_hadoop_binary,
                             hadoop_engine.which_hadoop_jar)
    archive_str = '-archives "%s"' % archive_path
    cmd_env_str = '-cmdenv LD_LIBRARY_PATH=%s' % ld_library_path
    #
    fs_str = '-fs "%s"' % hadoop_engine.hdfs_uri if hadoop_engine.hdfs_uri is not None else ''
    jt_str = '-jt "%s"' % hadoop_engine.jobtracker_uri if hadoop_engine.jobtracker_uri is not None else ''
    hadoop_cmd_str = ' '.join([
            jar_str,
            '-D mapred.task.timeout=%s' % task_timeout,
            '-D mapred.map.tasks=%s' % n_tasks,
            '-D mapred.child.java.opts=-Xmx8G',
            archive_str,
            fs_str,
	    jt_str,
            # fixme: need to prepend output_path to input_filename
            '-input "%s"' % os.path.join(hdfs_path, hadoop_engine.input_filename),
            '-output "%s"' % os.path.join(hdfs_path, hadoop_engine.output_path),
            '-mapper "%s"' % mapper_path,
            '-reducer /bin/cat',
            '-file %s' % hadoop_engine.table_data_filename,
            cmd_env_str,
            ])
    print hadoop_cmd_str
    return hadoop_cmd_str

def get_was_successful(output_path):
    success_file = os.path.join(output_path, '_SUCCESS')
    was_successful = os.path.isfile(success_file)
    return was_successful

def ensure_dir(dir):
  try:
    os.makedirs(dir)
  except:
    pass
  return

def send_hadoop_command(hadoop_engine, table_data_filename, input_filename,
                        output_path, n_tasks):
  # make sure output_path doesn't exist
  rm_hdfs(hadoop_engine.hdfs_uri, output_path, hdfs_base_dir=hadoop_engine.hdfs_dir)
  # send up input
  put_hdfs(hadoop_engine.hdfs_uri, input_filename, hdfs_base_dir=hadoop_engine.hdfs_dir)
  # actually send
  hadoop_cmd_str = create_hadoop_cmd_str(hadoop_engine, n_tasks=n_tasks)
  was_successful = None
  if DEBUG:
    print hadoop_cmd_str
  else:
    ensure_dir(output_path)
    output_path_dotdot = os.path.split(output_path)[0]
    out_filename = os.path.join(output_path_dotdot, 'out')
    err_filename = os.path.join(output_path_dotdot, 'err')
    redirect_str = ' >>%s 2>>%s'
    redirect_str %= (out_filename, err_filename)
    os.system(hadoop_cmd_str + redirect_str)
    # retrieve results
    get_hdfs(hadoop_engine.hdfs_uri, output_path,
             hdfs_base_dir=hadoop_engine.hdfs_dir)
    was_successful = get_was_successful(output_path)
  return was_successful
  
def write_hadoop_input():
    pass

def get_hadoop_output_filename(output_path):
    hadoop_output_filename = os.path.join(output_path, 'part-00000')
    return hadoop_output_filename
def read_hadoop_output_file(hadoop_output_filename):
    with open(hadoop_output_filename) as fh:
        ret_dict = dict([xu.parse_hadoop_line(line) for line in fh])
    return ret_dict
def read_hadoop_output(output_path):
    hadoop_output_filename = get_hadoop_output_filename(output_path)
    return read_hadoop_output_file(hadoop_output_filename)

def get_uris(base_uri, hdfs_uri, jobtracker_uri):
    if base_uri is not None:
        hdfs_uri = 'hdfs://%s:8020/' % base_uri
        jobtracker_uri = '%s:8021' % base_uri
    return hdfs_uri, jobtracker_uri
        
if __name__ == '__main__':
    import argparse
    #
    import tabular_predDB.python_utils.data_utils as du
    #
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str)
    parser.add_argument('--base_uri', type=str, default=None)
    parser.add_argument('--hdfs_uri', type=str, default=default_hdfs_uri)
    parser.add_argument('--jobtracker_uri', type=str,
                        default=default_jobtracker_uri)
    parser.add_argument('--hdfs_dir', type=str, default=default_hdfs_dir)
    parser.add_argument('-DEBUG', action='store_true')
    parser.add_argument('--which_engine_binary', type=str, default=default_engine_binary)
    parser.add_argument('--which_hadoop_binary', type=str, default=default_hadoop_binary)
    parser.add_argument('--which_hadoop_jar', type=str, default=default_hadoop_jar)
    parser.add_argument('--n_chains', type=int, default=4)
    parser.add_argument('--n_steps', type=int, default=1)
    parser.add_argument('--table_filename', type=str, default='../www/data/dha_small.csv')
    parser.add_argument('--resume_filename', type=str, default=None)
    parser.add_argument('--pkl_filename', type=str, default=None)
    #
    args = parser.parse_args()
    base_uri = args.base_uri
    hdfs_uri = args.hdfs_uri
    jobtracker_uri = args.jobtracker_uri
    hdfs_dir = args.hdfs_dir
    DEBUG = args.DEBUG
    which_engine_binary = args.which_engine_binary
    which_hadoop_binary = args.which_hadoop_binary
    which_hadoop_jar= args.which_hadoop_jar
    n_chains = args.n_chains
    n_steps = args.n_steps
    table_filename = args.table_filename
    resume_filename = args.resume_filename
    pkl_filename = args.pkl_filename
    command = args.command
    assert command in set(gu.get_method_names(HadoopEngine))

    hdfs_uri, jobtracker_uri = get_uris(base_uri, hdfs_uri, jobtracker_uri)
    T, M_r, M_c = du.read_model_data_from_csv(table_filename, gen_seed=0)
    he = HadoopEngine(which_engine_binary=which_engine_binary,
		      which_hadoop_binary=which_hadoop_binary,
		      which_hadoop_jar=which_hadoop_jar,
                      hdfs_dir=hdfs_dir, hdfs_uri=hdfs_uri,
                      jobtracker_uri=jobtracker_uri)
    
    X_L_list, X_D_list = None, None
    if command == 'initialize':
        hadoop_output = he.initialize(M_c, M_r, T,
                                      initialization='from_the_prior',
                                      n_chains=n_chains)
        if hadoop_output is not None:
            M_c, M_r, X_L_list, X_D_list = hadoop_output
    elif command == 'analyze':
        assert resume_filename is not None
        if fu.is_pkl(resume_filename):
          resume_dict = fu.unpickle(resume_filename)
        else:
          resume_dict = read_hadoop_output_file(resume_filename)
        X_L_list = resume_dict['X_L_list']
        X_D_list = resume_dict['X_D_list']
        hadoop_output = he.analyze(M_c, T, X_L_list, X_D_list,
                                   n_steps=n_steps)
        if hadoop_output is not None:
            X_L_list, X_D_list = hadoop_output
    else:
        print 'Unknown command: %s' % command
        sys.exit()
        
    if pkl_filename is not None:
      to_pkl_dict = dict(
            T=T,
            M_c=M_c,
            M_r=M_r,
            X_L_list=X_L_list,
            X_D_list=X_D_list,
            )
      fu.pickle(to_pkl_dict, filename=pkl_filename)
