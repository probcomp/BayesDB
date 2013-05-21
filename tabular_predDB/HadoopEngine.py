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
import tabular_predDB.EngineTemplate as EngineTemplate


default_which_binary = "hadoop_line_processor"
default_hdfs_dir = "/user/bigdata/SSCI/test_remote_streaming/"
default_jobtracker_uri = "xd-jobtracker.xdata.data-tactics-corp.com:8021"
default_hdfs_uri = "hdfs://xd-namenode.xdata.data-tactics-corp.com:8020/"
default_which_hadoop_jar = "/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.0.0-mr1-cdh4.1.2.jar"


class HadoopEngine(object):

    def __init__(self, seed=0,
                 which_binary=default_which_binary,
                 hdfs_dir=default_hdfs_dir,
                 jobtracker_uri=default_jobtracker_uri,
                 hdfs_uri=default_hdfs_uri,
                 which_hadoop_jar=default_which_hadoop_jar,
                 ):
        super(HadoopEngine, self).__init__(seed)
        self.which_binary = which_binary
        self.hdfs_dir = self.default_hdfs_dir
        self.jobtracker_uri = self.default_jobtracker_uri
        self.hdfs_uri = self.default_hdfs_uri
        self.which_hadoop_jar = self.default_which_hadoop_jar
        return

    def initialize(self, M_c, M_r, T, initialization='from_the_prior'):
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

def send_hadoop_command():
    pass

def write_hadoop_input():
    pass

def read_hadoop_output():
    pass
