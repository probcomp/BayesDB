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
import tabular_predDB.python_utils.hadoop_utils as hu


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
default_engine_binary = "/user/bigdata/SSCI/hadoop_line_processor.jar"
default_hdfs_dir = "/user/bigdata/SSCI/"
default_output_path = 'myOutputDir'
default_input_filename = 'hadoop_input'
default_table_data_filename = xu.default_table_data_filename


class HadoopEngine(object):

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
                 one_map_task_per_line=True,
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
        self.one_map_task_per_line = one_map_task_per_line
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
      was_successful = hu.send_hadoop_command(self,
                                              table_data_filename,
                                              input_filename, output_path,
                                              n_tasks=n_chains)
      hadoop_output = None
      if was_successful:
        X_L_list, X_D_list = hu.read_hadoop_output(output_path,
                                                   'initialize_output')
        hadoop_output = M_c, M_r, X_L_list, X_D_list
      return hadoop_output

    def analyze(self, M_c, T, X_L, X_D, kernel_list=(), n_steps=1, c=(), r=(),
                max_iterations=-1, max_time=-1, **kwargs):  
        output_path = self.output_path
        input_filename = self.input_filename
        table_data_filename = self.table_data_filename
        xu.assert_vpn_is_connected()
        #
        analyze_args_dict = dict(command='analyze', kernel_list=kernel_list,
                                 n_steps=n_steps, c=c, r=r, max_time=max_time)
        # chunk_analyze is a special case of analyze
        if 'chunk_size' in kwargs:
          chunk_size = kwargs['chunk_size']
          chunk_filename_prefix = kwargs['chunk_filename_prefix']
          chunk_dest_dir = kwargs['chunk_dest_dir']
          analyze_args_dict['command'] = 'chunk_analyze'
          analyze_args_dict['chunk_size'] = chunk_size
          analyze_args_dict['chunk_filename_prefix'] = chunk_filename_prefix
          # WARNING: chunk_dest_dir MUST be writeable by hadoop user mapred
          analyze_args_dict['chunk_dest_dir'] = chunk_dest_dir

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
        was_successful = hu.send_hadoop_command(self,
                                                table_data_filename,
                                                input_filename, output_path,
                                                n_tasks=len(X_L))
        hadoop_output = None
        if was_successful:
          X_L_list, X_D_list = hu.read_hadoop_output(output_path,
                                                     'analyze_output')
          hadoop_output = X_L_list, X_D_list
        return hadoop_output

    def simple_predictive_sample(self, M_c, X_L, X_D, Y, Q, n=1):
        pass

    def impute(self, M_c, X_L, X_D, Y, Q, n):
        pass

    def impute_and_confidence(self, M_c, X_L, X_D, Y, Q, n):
        pass

        
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
    parser.add_argument('--chunk_size', type=int, default=1)
    parser.add_argument('--chunk_filename_prefix', type=str, default='chunk')
    parser.add_argument('--chunk_dest_dir', type=str, default='/user/bigdata/SSCI/chunk_dir')
    parser.add_argument('--max_time', type=float, default=-1)
    parser.add_argument('--table_filename', type=str, default='../www/data/dha_small.csv')
    parser.add_argument('--resume_filename', type=str, default=None)
    parser.add_argument('--pkl_filename', type=str, default=None)
    parser.add_argument('--cctypes_filename', type=str, default=None)
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
    chunk_size = args.chunk_size
    chunk_filename_prefix = args.chunk_filename_prefix
    chunk_dest_dir = args.chunk_dest_dir
    max_time = args.max_time
    table_filename = args.table_filename
    resume_filename = args.resume_filename
    pkl_filename = args.pkl_filename
    #
    command = args.command
    # assert command in set(gu.get_method_names(HadoopEngine))
    #
    cctypes_filename = args.cctypes_filename
    cctypes = None
    if cctypes_filename is not None:
      cctypes = fu.unpickle(cctypes_filename)

    hdfs_uri, jobtracker_uri = hu.get_uris(base_uri, hdfs_uri, jobtracker_uri)
    T, M_r, M_c = du.read_model_data_from_csv(table_filename, gen_seed=0,
                                              cctypes=cctypes)
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
          resume_dict = hu.read_hadoop_output_file(resume_filename)
        X_L_list = resume_dict['X_L_list']
        X_D_list = resume_dict['X_D_list']
        hadoop_output = he.analyze(M_c, T, X_L_list, X_D_list,
                                   n_steps=n_steps, max_time=max_time)
        if hadoop_output is not None:
            X_L_list, X_D_list = hadoop_output
    elif command == 'chunk_analyze':
        assert resume_filename is not None
        if fu.is_pkl(resume_filename):
          resume_dict = fu.unpickle(resume_filename)
          X_L_list = resume_dict['X_L_list']
          X_D_list = resume_dict['X_D_list']
        else:
          X_L_list, X_D_list = hu.read_hadoop_output(resume_filename)
        hadoop_output = he.analyze(M_c, T, X_L_list, X_D_list,
                                   n_steps=n_steps, max_time=max_time,
                                   chunk_size=chunk_size,
                                   chunk_filename_prefix=chunk_filename_prefix,
                                   chunk_dest_dir=chunk_dest_dir)
        if hadoop_output is not None:
            X_L_list, X_D_list = hadoop_output
    else:
        print 'Unknown command: %s' % command
        import sys
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
