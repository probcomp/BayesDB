import itertools as it
import time

import argparse
import numpy
import tempfile 
import parse_mi
import pickle

import os

import tabular_predDB.cython_code.State as State
import tabular_predDB.python_utils.hadoop_utils as hu
import tabular_predDB.python_utils.file_utils as fu
import tabular_predDB.python_utils.xnet_utils as xu
import tabular_predDB.LocalEngine as LE
import tabular_predDB.HadoopEngine as HE

import impute_test_local

def generate_hadoop_dicts(which_kernels, impute_run_parameters, args_dict):
    for which_kernel in which_kernels:
        kernel_list = (which_kernel, )
        dict_to_write = dict(impute_run_parameters)
        dict_to_write.update(args_dict)
        # must write kernel_list after update
        dict_to_write['kernel_list'] = kernel_list
        yield dict_to_write

def write_hadoop_input(input_filename, impute_run_parameters, SEED):
    # prep settings dictionary
    impute_analyze_args_dict = xu.default_analyze_args_dict
    impute_analyze_args_dict['command'] = 'impute_analyze'
    with open(input_filename, 'a') as out_fh:
        xu.write_hadoop_line(out_fh, key=SEED, dict_to_write=impute_run_parameters)

# Run
if __name__ == '__main__':

	default_num_rows_list = [100, 500, 1000] 
	default_num_cols_list = [8, 16, 32]	
	default_num_clusters_list = [5, 25, 50]	
	default_num_splits_list = [1, 2, 4, 8]
	default_mean_ranges_list = [.5, 1, 2]
	default_correlation_list = [.1, .25, .5, .75]
	
	#
	parser = argparse.ArgumentParser()
	parser.add_argument('--gen_seed', type=int, default=0)
	parser.add_argument('--num_datasets', type=int, default=5)
	parser.add_argument('--num_chains', type=int, default=10)
	parser.add_argument('--burn_in', type=int, default=200)
	parser.add_argument('--which_engine_binary', type=str,
	        default=HE.default_engine_binary)
	parser.add_argument('-do_local', action='store_true')
	parser.add_argument('-do_remote', action='store_true')
	parser.add_argument('--num_rows_list', type=int, nargs='*',
	        default=default_num_rows_list)
	parser.add_argument('--num_cols_list', type=int, nargs='*',
	        default=default_num_cols_list)
	parser.add_argument('--num_clusters_list', type=int, nargs='*',
	        default=default_num_clusters_list)
	parser.add_argument('--num_splits_list', type=int, nargs='*',
	        default=default_num_splits_list)
	parser.add_argument('--corr_list', type=float, nargs='*',
	        default=default_correlation_list)

	#
	args = parser.parse_args()
	data_seed = args.gen_seed
	do_local = args.do_local
	do_remote = args.do_remote
	burn_in = args.burn_in
	num_chains = args.num_chains
	num_datasets = args.num_datasets
	num_rows_list = args.num_rows_list
	num_cols_list = args.num_cols_list
	num_clusters_list = args.num_clusters_list
	num_splits_list = args.num_splits_list
	corr_list = args.corr_list
	which_engine_binary = args.which_engine_binary
	#
	print 'using burn_in: %i' % burn_in
	print 'using num_rows_list: %s' % num_rows_list
	print 'using num_cols_list: %s' % num_cols_list
	print 'using num_clusters_list: %s' % num_clusters_list
	print 'using num_splits_list: %s' % num_splits_list
	print 'using delprop_list: %s' % corr_list
	print 'using engine_binary: %s' % which_engine_binary
	time.sleep(2)

	dirname = 'mi_analysis'
	fu.ensure_dir(dirname)
	directory_path = tempfile.mkdtemp(prefix='mi_analysis_',
                                dir=dirname)

	print 'output sent to %s' % directory_path

	output_path = os.path.join(directory_path, 'output')
	output_filename = os.path.join(directory_path, 'hadoop_output')
	table_data_filename = os.path.join(directory_path, 'table_data.pkl.gz')

	assert(os.path.exists(directory_path))
	
	input_filename = os.path.join(directory_path, "hadoop_input")
	params_filename = os.path.join(directory_path, "test_params.pkl")
	key_filename = os.path.join(directory_path, "test_key.pkl")
	
	# create a parameters dict
	params_dict = {
		'n_rows' 	  : num_rows_list,
		'n_clusters'  : num_clusters_list,
		'n_cols' 	  : num_cols_list,
		'n_splits' 	  : num_splits_list,
		'corr' 	  	  : corr_list,
		'n_iters' 	  : repeat_times,
		'n_chains' 	  : num_chains,
		'n_datasets'  : num_datasets,
		'burn_in' 	  : burn_in
		'max_index'   : 0
	}

	# save the params file as pickle
	try:
		pd_file = open( params_filename, "wb" )
	except IOError as err:
		print "Could not create %s. " % params_filename, err
		raise

	pickle.dump( params_dict, pd_file )
	pd_file.close()

	# cartesian product of test parameters. 
	tests = list(it.product(*[num_rows_list, num_clusters_list, num_cols_list, num_splits_list, corr_list]))

	testlist = []
	
	print "Writing tests file."	
	test_idx = 0
	for n_rows, n_clusters, n_cols, n_splits, corr in tests:	
		if numpy.mod(n_rows, n_clusters) == 0 and numpy.mod(n_cols,n_splits)==0:
			for dataset in range(num_datasets):
				for chain in range(num_chains):
					impute_run_parameters = dict(
							id=test_idx,
							dataset=dataset,
							sample=chain,
							num_clusters=n_clusters,
							num_rows=n_rows,
							num_cols=n_cols,
							num_views=n_splits,
							corr=corr,
							burn_in=burn_in,
							SEED=data_seed+test_idx+itr,
						)

					write_hadoop_input(input_filename, impute_run_parameters, SEED=data_seed+test_idx+itr)
					if do_local:
						testlist.append(impute_run_parameters)
			test_idx += 1
	
	print "Done."
	
	# table data is empty because we generate it in the mapper
	table_data=dict(T=[],M_c=[],X_L=[],X_D=[])
	fu.pickle(table_data, table_data_filename)

	#####################

	if do_local:
		output_filename = os.path.join(directory_path, "output_local")
		output_file_object = open(output_filename, 'ab')
		with open(input_filename,'rb') as infile:
			for line in infile:
				key, test_dict = xu.parse_hadoop_line(line)
				ret_dict = impute_test_local.impute_test_local(test_dict, output_file_object)
				xu.write_hadoop_line(output_file_object, key, ret_dict)
				print "%s\n\t%s" % (str(test_dict), str(ret_dict))

		output_file_object.close()
		# generate the csv
		parse_impute.parse_data_to_csv(input_filename, params_dict, test_idx, output_filename)
		print "Done."
	elif do_remote:
		# generate the massive hadoop files
		hadoop_engine = HE.HadoopEngine(output_path=output_path,
                                    input_filename=input_filename,
                                    table_data_filename=table_data_filename,
                                    which_engine_binary=which_engine_binary,
                                    )
	
		xu.write_support_files(table_data, hadoop_engine.table_data_filename,
	                              dict(command='mi_analyze'), hadoop_engine.command_dict_filename)
		t_start = time.time()
		hadoop_engine.send_hadoop_command(n_tasks=len(testlist))
		was_successful = hadoop_engine.get_hadoop_results()
		if was_successful:
			t_end = time.time()
			t_total = t_end-t_start
			print "That took %i seconds." % t_total
			hu.copy_hadoop_output(hadoop_engine.output_path, output_filename)
			parse_impute.parse_data_to_csv(input_filename, params_dict, test_idx, output_filename)
		else:
			print "Hadoop job was NOT successful. Check %s" % output_path