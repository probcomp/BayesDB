import os
#
import tabular_predDB.python_utils.xnet_utils as xu


def rm_hdfs(hdfs_uri, path, hdfs_base_dir='', DEBUG=False):
    rm_infix_args = '-rmr'
    # rm_infix_args = '-rm -r -f'
    hdfs_path = os.path.join(hdfs_base_dir, path)
    fs_str = ('-fs "%s"' % hdfs_uri) if hdfs_uri is not None else ''
    cmd_str = 'hadoop fs %s %s %s >rm_hdfs.out 2>rm_hdfs.err'
    cmd_str %= (fs_str, rm_infix_args, hdfs_path)
    if DEBUG:
        print cmd_str
        return cmd_str
    else:
        os.system(cmd_str)
    return

def get_hdfs(hdfs_uri, path, hdfs_base_dir='', DEBUG=False):
    hdfs_path = os.path.join(hdfs_base_dir, path)
    # clear local path
    rm_local(path)
    # get from hdfs
    fs_str = ('-fs "%s"' % hdfs_uri) if hdfs_uri is not None else ''
    cmd_str = 'hadoop fs %s -get %s %s'
    cmd_str %= (fs_str, hdfs_path, path)
    if DEBUG:
        print cmd_str
        return cmd_str
    else:
        os.system(cmd_str)
    return

def ensure_dir_hdfs(fs_str, hdfs_path, DEBUG=False):
  dirname = os.path.split(hdfs_path)[0]
  cmd_str = 'hadoop fs %s -mkdir %s'
  cmd_str %= (fs_str, dirname)
  if DEBUG:
    print cmd_str
    return cmd_str
  else:
    os.system(cmd_str)
  return

def put_hdfs(hdfs_uri, path, hdfs_base_dir='', DEBUG=False):
    hdfs_path = os.path.join(hdfs_base_dir, path)
    # clear hdfs path
    rm_hdfs(hdfs_uri, path, hdfs_base_dir)
    # put to hdfs
    fs_str = ('-fs "%s"' % hdfs_uri) if hdfs_uri is not None else ''
    ensure_dir_hdfs(fs_str, hdfs_path)
    cmd_str = 'hadoop fs %s -put %s %s >put_hdfs.out 2>put_hdfs.err'
    cmd_str %= (fs_str, path, hdfs_path)
    if DEBUG:
        print cmd_str
        return cmd_str
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
    #
    input_format_str = '-inputformat org.apache.hadoop.mapred.lib.NLineInputFormat' if hadoop_engine.one_map_task_per_line else ''
    hadoop_cmd_str = ' '.join([
            jar_str,
            '-D mapred.task.timeout=%s' % task_timeout,
            '-D mapred.map.tasks=%s' % n_tasks,
            '-D mapred.child.java.opts=-Xmx8G',
            archive_str,
            fs_str,
	    jt_str,
            input_format_str,
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

def send_hadoop_command(hadoop_engine, table_data_filename, input_filename,
                        output_path, n_tasks, DEBUG=False):
  # make sure output_path doesn't exist
  rm_hdfs(hadoop_engine.hdfs_uri, output_path, hdfs_base_dir=hadoop_engine.hdfs_dir)
  # send up input
  put_hdfs(hadoop_engine.hdfs_uri, input_filename, hdfs_base_dir=hadoop_engine.hdfs_dir)
  # actually send
  hadoop_cmd_str = create_hadoop_cmd_str(hadoop_engine, n_tasks=n_tasks)
  was_successful = None
  if DEBUG:
    print hadoop_cmd_str
    return hadoop_cmd_str
  else:
    ensure_dir(output_path)
    output_path_dotdot = os.path.split(output_path)[0]
    out_filename = os.path.join(output_path_dotdot, 'out')
    err_filename = os.path.join(output_path_dotdot, 'err')
    redirect_str = '>>%s 2>>%s'
    redirect_str %= (out_filename, err_filename)
    # could I nohup and check hdfs for presence of _SUCCESS every N seconds?
    # cmd_str = ' '.join(['nohup', hadoop_cmd_str, redirect_str, '&'])
    cmd_str = ' '.join([hadoop_cmd_str, redirect_str])
    os.system(cmd_str)
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
def read_hadoop_output(output_path, copy_to_filename=None):
    hadoop_output_filename = get_hadoop_output_filename(output_path)
    if copy_to_filename is not None:
      cmd_str = 'cp %s %s' % (hadoop_output_filename, copy_to_filename)
      os.system(cmd_str)
    hadoop_output = read_hadoop_output_file(hadoop_output_filename)
    X_L_list = [el['X_L'] for el in hadoop_output.values()]
    X_D_list = [el['X_D'] for el in hadoop_output.values()]
    return X_L_list, X_D_list

def get_uris(base_uri, hdfs_uri, jobtracker_uri):
    if base_uri is not None:
        hdfs_uri = 'hdfs://%s:8020/' % base_uri
        jobtracker_uri = '%s:8021' % base_uri
    return hdfs_uri, jobtracker_uri
