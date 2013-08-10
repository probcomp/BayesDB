import sys
import csv
import os
#
import numpy
#
import tabular_predDB.python_utils.xnet_utils as xu

def parsed_line_to_output_row(parsed_line):
  ret_list = [
      int(parsed_line[0]),
      parsed_line[1]['num_rows'],
      parsed_line[1]['num_cols'],
      parsed_line[1]['num_views'],
      parsed_line[1]['num_clusters'],
      parsed_line[1]['n_steps'],
      parsed_line[1]['block_size'],
      parsed_line[1]['ari_views'],
      parsed_line[1]['ari_table'],
      ]
  return ret_list

def parse_to_csv(in_filename, out_filename='parsed_convergence.csv'):
    header = ['experiment', 'num_rows', 'num_cols', 'num_clusters', 'num_views', 'num_steps',
        'block_size','ari_views', 'ari_table']
    with open(in_filename) as in_fh:
      with open(out_filename,'w') as out_fh:
        csvwriter = csv.writer(out_fh)
	csvwriter.writerow(header)
        for line in in_fh:
            try:
              parsed_line = xu.parse_hadoop_line(line)
              csvwriter.writerow(parsed_line_to_output_row(parsed_line))
            except Exception, e:
              sys.stderr.write(line + '\n' + str(e) + '\n')
