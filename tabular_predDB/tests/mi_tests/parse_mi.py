import numpy
import csv
import os
import ast
import pickle

import tabular_predDB.python_utils.inference_utils as iu
import tabular_predDB.python_utils.xnet_utils as xu

import pdb

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

	header = ['id', 'num_rows', 'num_cols', 'num_views', 'num_clusters', 'corr','MI','Linfoot']

	# data_mi = [[[0] for i in range(n_datasets)] for i in range(n_tests)]
	# data_linfoot = [[[0] for i in range(n_datasets)] for i in range(n_tests)]
	# counts = [[[0] for i in range(n_datasets)] for i in range(n_tests)]

	data_mi = [0.0]*n_tests
	data_linfoot = [0.0]*n_tests
	counts = [0.0]*n_tests


	for result in results:
		res = result[1] # because it's a tuple with an id at index 0
		test_idx = res['id']
		test_dataset = res['dataset']
		test_sample = res['sample']
		
		data_mi[test_idx] += float(res['mi']) 
		data_linfoot[test_idx] += float(iu.mutual_information_to_linfoot(res['mi']))
		counts[test_idx] += 1.0
	
	for test_ids in range(n_tests):
		data_mi[test_idx] /= counts[test_idx]
		data_linfoot[test_idx] /= counts[test_idx]

	# # calculate the mean over samples
	# for test in range(n_tests):
		
	# 	for dataset in range(n_datasets):
	# 		try:
	# 			data_mi[test][dataset] = numpy.array(data_mi[test][dataset],dtype=float)
	# 		except ValueError:
	# 			pdb.set_trace()

	# 		try:
	# 			data_mi[test][dataset] = numpy.mean(data_mi[test][dataset],axis=0)
	# 		except TypeError:
	# 			pdb.set_trace()

	# 		data_linfoot[test][dataset] = mi_to_linfoot(data_mi[test][dataset])

	# 		data_mi[test][dataset] = numpy.mean(data_mi[test][dataset])
	# 		data_linfoot[test][dataset] = numpy.mean(data_linfoot[test][dataset])

	# 	# now calculate the mean over datasets
	# 	data_mi[test] = numpy.mean(numpy.array(data_mi[test]))
	# 	data_linfoot[test] = numpy.mean(numpy.array(data_linfoot[test]))
	
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
				line = parse_line(res, data_mi[test_idx], data_linfoot[test_idx])
				csvwriter.writerow(line)

def mi_to_linfoot(mi):
	#
	# linfoot = numpy.zeros(mi.shape)
	# if len(mi.shape) == 1:
	# 	for entry in range(mi.size):
	# 		linfoot[entry] = iu.mutual_information_to_linfoot(mi[entry])
	# else:
	# 	for r in range(mi.shape[0]):
	# 		for c in range(mi.shape[1]):
	# 			linfoot[r,c] = iu.mutual_information_to_linfoot(mi[r,c])


	# return linfoot
	return [iu.mutual_information_to_linfoot(m) for m in mi]

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
	n_tests = args.n_tests
	params_filename = args.params_filename
	params_dict = pickle.load( open( params_filename, "rb" ))



	parse_data_to_csv(key_filename, params_dict, n_tests, output_filename)

