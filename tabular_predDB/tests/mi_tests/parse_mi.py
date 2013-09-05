import numpy
import csv
import os
import ast
import pickle

import tabular_predDB.python_utils.inference_utils as iu
import tabular_predDB.python_utils.xnet_utils as xu

def is_hadoop_file(filename):
	name, extension = os.path.splitext(filename)
	if extension is 'gz':
		return True
	else:
		return False

def parse_line(test, mi, linfoot):
	index = test['id']
	num_rows = test['num_rows']
	num_cols = test['num_cols']
	num_views = test['num_views']
	num_clusters = test['num_clusters']
	corr = test['corr']
	
	row = [index, num_rows, num_cols, num_views, num_clusters, corr, mi, linfoot]

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

	data_mi = numpy.zeros((n_tests, n_samples*n_datasets))	

	for result in results:
		res = result[1] # because it's a tuple with an id at index 0
		test_idx = res['id']
		test_dataset = res['dataset']
		test_sample = res['sample']
		data_mi[test_idx, test_dataset*n_datasets+test_sample] += res['mi']


	# get the mean over datasets and samples
	mean_mi = numpy.mean(data_mi,axis=1)
	mean_linfoot = mi_to_linfoot(mean_mi)
	
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
				line = parse_line(res, mean_mi[test_idx], mean_linfoot[test_idx])
				csvwriter.writerow(line)

def mi_to_linfoot(mi):
	#
	linfoot = numpy.zeros(mi.shape)
	for r in range(mi.shape[0]):
		for c in range(mi.shape[1]):
			linfoot[r,c] = iu.mutual_information_to_linfoot(mi[r,c])

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

