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


class HadoopEngine(object):

    def __init__(self, seed=0,
                 which_engine_binary=default_which_engine_binary,
                 hdfs_dir=default_hdfs_dir,
                 jobtracker_uri=default_jobtracker_uri,
                 hdfs_uri=default_hdfs_uri,
                 which_hadoop_jar=default_which_hadoop_jar,
                 ):
        # assert_vpn_is_connected()
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
        #
        table_data = dict(M_c=M_c, M_r=M_r, T=T)
        xu.pickle_table_data(table_data, table_data_filename)
        xu.write_initialization_files(input_filename, n_chains)
        put_hdfs(self.hdfs_uri, input_filename, hdfs_base_dir=self.hdfs_dir)
        put_hdfs(self.hdfs_uri, table_data_filename,
                 hdfs_base_dir=self.hdfs_dir)
        pass

    def analyze(self, M_c, T, X_L, X_D, kernel_list=(), n_steps=1, c=(), r=(),
                max_iterations=-1, max_time=-1):
        pass

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

def get_hdfs(hdfs_uri, path, hdfs_base_dir=''):
    hdfs_path = os.path.join(hdfs_base_dir, path)
    # clear local path
    cmd_str = 'rm -rf %s'
    cmd_str %= path
    os.system(cmd_str)
    # get from hdfs
    cmd_str = 'hadoop fs -fs %s -get %s %s'
    cmd_str %= (hdfs_uri, hdfs_path, path)
    os.system(cmd_str)
    return

def put_hdfs(hdfs_uri, path, hdfs_base_dir=''):
    hdfs_path = os.path.join(hdfs_base_dir, path)
    # clear hdfs path
    cmd_str = 'hadoop fs -fs %s -rm -r -f %s'
    cmd_str %= (hdfs_uri, hdfs_path)
    os.system(cmd_str)
    # put to hdfs
    cmd_str = 'hadoop fs -fs %s -put %s %s'
    cmd_str %= (hdfs_uri, path, hdfs_path)
    os.system(cmd_str)
    #
    return

def create_hadoop_cmd_str(hadoop_engine, task_timeout, n_chains):
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
            '-D mapred.map.tasks=%s' % n_chains,
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

def send_hadoop_command():
    pass

def write_hadoop_input():
    pass

def read_hadoop_output():
    pass

# comamnd creation logic from send_hadoop_command.sh
# $HADOOP_HOME/bin/hadoop jar "$WHICH_HADOOP_JAR" \
#     -D mapred.task.timeout="${task_timeout_in_ms}" \
#     -D mapred.map.tasks="${num_map_tasks}" \
#     -archives "${HDFS_URI}${HDFS_DIR}${WHICH_ENGINE_BINARY}.jar" \
#     -fs "$HDFS_URI" -jt "$JOBTRACKER_URI" \
#     -input "${HDFS_URI}${HDFS_DIR}hadoop_input" \
#     -output "${HDFS_URI}${HDFS_DIR}myOutputDir/" \
#     -mapper ${WHICH_ENGINE_BINARY}.jar/${WHICH_ENGINE_BINARY} \
#     -reducer /bin/cat \
#     -file hadoop_input \
#     -file table_data.pkl.gz \
#     -cmdenv LD_LIBRARY_PATH=./${WHICH_ENGINE_BINARY}.jar/:$LD_LIBRARY_PATH

# actual command from send_hadoop_command.sh
#
# /bin/hadoop jar /usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.1.2.jar -D mapred.task.timeout=600000 -D mapred.map.tasks= -archives hdfs://xd-namenode.xdata.data-tactics-corp.com:8020//user/bigdata/SSCI/test_remote_streaming/hadoop_line_processor.jar -fs hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/ -jt xd-jobtracker.xdata.data-tactics-corp.com:8021 -input hdfs://xd-namenode.xdata.data-tactics-corp.com:8020//user/bigdata/SSCI/test_remote_streaming/hadoop_input -output hdfs://xd-namenode.xdata.data-tactics-corp.com:8020//user/bigdata/SSCI/test_remote_streaming/myOutputDir/ -mapper hadoop_line_processor.jar/hadoop_line_processor -reducer /bin/cat -file hadoop_input -file table_data.pkl.gz -cmdenv LD_LIBRARY_PATH=./hadoop_line_processor.jar/:


# command created from create_hadoop_cmd_str
#
# 'bin/hadoop jar /usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.1.2.jar -D mapred.task.timeout=1 -D mapred.map.tasks=2 -archives "hdfs://xd-namenode.xdata.data-tactics-corp.com:8020//user/bigdata/SSCI/test_remote_streaming/hadoop_line_processor.jar" -fs "hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/" -jt "xd-jobtracker.xdata.data-tactics-corp.com:8021" -input "hdfs://xd-namenode.xdata.data-tactics-corp.com:8020//user/bigdata/SSCI/test_remote_streaming/hadoop_input" -output "hdfs://xd-namenode.xdata.data-tactics-corp.com:8020//user/bigdata/SSCI/test_remote_streaming/myOutputDir" -mapper "hadoop_line_processor.jar/hadoop_line_processor" -reducer /bin/cat -file hadoop_input -file table_data.pkl.gz -cmdenv LD_LIBRARY_PATH=./hadoop_line_processor.jar:'

if __name__ == '__main__':
    he = HadoopEngine()
    print create_hadoop_cmd_str(he, 1, 2)
