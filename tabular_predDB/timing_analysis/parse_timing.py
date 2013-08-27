import sys
import csv
import os
#
import numpy
#
import tabular_predDB.python_utils.xnet_utils as xu


def assert_row_clustering_count_same(row_cluster_counts):
    baseline = numpy.array(row_cluster_counts[0])
    for row_cluster_count in row_cluster_counts[1:]:
        row_cluster_count = numpy.array(row_cluster_count)
        assert all(baseline==row_cluster_count)
    return

def assert_dims_same(start_dims, end_dims):
    start_num_views = start_dims[0]
    end_num_views = end_dims[0]
    assert start_num_views == end_num_views
    #
    start_row_clustering = numpy.array(start_dims[1])
    end_row_clustering = numpy.array(end_dims[1])
    assert (start_row_clustering == end_row_clustering).all()
    return

def parse_reduced_dims(reduced_line):
    start_dims = reduced_line['start_dims']
    end_dims = reduced_line['end_dims']
    start_row_cluster_counts = start_dims[1]
    assert_row_clustering_count_same(start_row_cluster_counts)
    assert_dims_same(start_dims, end_dims)
    #
    start_num_views = start_dims[0]
    start_num_clusters = len(start_dims[1][0])
    return start_num_clusters, start_num_views

def parse_reduced_line(reduced_line):
    num_clusters, num_views = parse_reduced_dims(reduced_line)
    (num_rows, num_cols) = reduced_line['table_shape']
    kernel_list = reduced_line['kernel_list']
    assert len(kernel_list) == 1
    which_kernel = kernel_list[0]
    time_per_step = reduced_line['elapsed_secs'] / reduced_line['n_steps']
    return num_rows, num_cols, num_clusters, num_views, \
        time_per_step, which_kernel

def parse_timing_to_csv(filename, outfile='parsed_timing.csv'):
   #drive, path = os.path.splitdrive(filename)
   #outpath, file_nameonly = os.path.split(path)

   with open(filename) as fh:
        lines = []
        for line in fh:
            lines.append(xu.parse_hadoop_line(line))

   header = ['num_rows', 'num_cols', 'num_clusters', 'num_views', 'time_per_step', 'which_kernel']
   
   reduced_lines = map(lambda x: x[1], lines)
      
   with open(outfile,'w') as csvfile:
	csvwriter = csv.writer(csvfile,delimiter=',')
	csvwriter.writerow(header)
    	for reduced_line in reduced_lines:
            try:
            	parsed_line = parse_reduced_line(reduced_line)
	    	csvwriter.writerow(parsed_line)
            except Exception, e:
                pass


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str)
    args = parser.parse_args()
    filename = args.filename

    with open(filename) as fh:
        lines = []
        for line in fh:
            lines.append(xu.parse_hadoop_line(line))

    header = 'num_rows, num_cols, num_clusters, num_views, time_per_step, which_kernel'
    print header
    reduced_lines = map(lambda x: x[1], lines)
    for reduced_line in reduced_lines:
        try:
            parsed_line = parse_reduced_line(reduced_line)
            print ','.join(map(str, parsed_line))
        except Exception, e:
            pass

