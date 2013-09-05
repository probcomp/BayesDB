import numpy
import csv
import os
import ast
import pickle

import tabular_predDB.python_utils.xnet_utils as xu

def is_hadoop_file(filename):
	name, extension = os.path.splitext(filename)
	if extension is 'gz':
		return True
	else:
		return False

def parse_line(test, mean_impute, stderr_impute, mean_colave, stderr_colave):
	index = test['id']
	num_rows = test['num_rows']
	num_cols = test['num_cols']
	num_views = test['num_views']
	num_clusters = test['num_clusters']
	mean_range = test['mean_range']
	delete_prop = test['del_prop']

	row = [index, num_rows, num_cols, num_views, num_clusters, mean_range, delete_prop,
		mean_impute, stderr_impute, mean_colave, stderr_colave]

	return row

def hadoop_to_dict_generator(test_key_file_object):
	# return read cursor to the start (or this generator cannot be called again)
	test_key_file_object.seek(0)
	for line in test_key_file_object:
		dict_line = xu.parse_hadoop_line(line)
		yield dict_line
	
def parse_data_to_csv(test_key_filename, params_dict, n_tests, output_filename):
	# open input file and convert to list of dicts
	test_key_file_object = open(test_key_filename, 'rb')
	input_lines = hadoop_to_dict_generator(test_key_file_object)

	# open output file and convert to list of dicts
	output_file_object = open(output_filename, 'rb')
	results = hadoop_to_dict_generator(output_file_object)
	
	n_datasets = params_dict['n_datasets']
	n_samples = params_dict['n_samples']

	header = ['id', 'num_rows', 'num_cols', 'num_views', 'num_splits', 'corr','MI','Linfoot']

	data_mi = numpy.zeros((n_tests, n_iters*n_chains))

	test_data = [0]*n_tests

	for result in results:
		res = result[1] # because it's a tuple with an id at index 0
		test_idx = res['id']
		test_dataset = res['dataset']
		test_sample = res['sample']
		data_mi[test_idx, test_dataset*n_iters+test_sample] += res['mi']

	data_linfoot = mi_to_linfoot(data_mi)

	# get the mean and standard error over test repeats
	mean_mi = numpy.mean(data_mi,axis=1)
	stderr_mi = numpy.std(data_mi,axis=1)/(float(n_iters*n_chains)**0.5)


	name, extension = os.path.splitext(output_filename)

	outfile = name + '.csv'

	with open(outfile,'w') as csvfile:
		csvwriter = csv.writer(csvfile,delimiter=',')
		csvwriter.writerow(header)
		current_idx = -1
		for test in input_lines:
			res = test[1]
			test_idx = res['id']
			if test_idx != current_idx:
				current_idx = test_idx
				line = parse_line(res, mean_impute[test_idx], stderr_impute[test_idx], mean_colave[test_idx], stderr_colave[test_idx])
				csvwriter.writerow(line)

if __name__ == "__main__":

	import argparse
	parser = argparse.ArgumentParser()

	parser.add_argument('--key_filename', type=str)
	parser.add_argument('--params_filename', type=str)
	parser.add_argument('--n_tests', type=int)
	parser.add_argument('--output_filename', type=str)

	args = parser.parse_args()

	key_filename = args.key_filename
	output_filename = args.output_filename
	n_iters = args.n_iters
	n_chains = args.n_chains


	parse_data_to_csv(key_filename, params_dict, n_tests, output_filename)

