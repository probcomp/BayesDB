import unittest
import experiment_utils as eu
import experiment_runner.experiment_utils as eru
from experiment_runner.ExperimentRunner import ExperimentRunner, propagate_to_s3 

# import each test
import haystacks_break
import fills_in_the_blanks
import estimate_the_full_joint
import recovers_original_densities
import error_bars_shrink_with_more_iters

class RunExperiments(unittest.TestCase):

	def run_error_bars_shrink_with_more_iters(self):
		results_filename = 'error_bars_shrink_results'
	    dirname_prefix = 'error_bars_shrink'

		parser = error_bars_shrink_with_more_iters.gen_parser()
	    args = parser.parse_args()

	    argsdict = eu.parser_args_to_dict(args)

		er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, 
			bucket_str='experiment_runner', storage_type='fs')

		er.do_experiments([argsdict], do_multiprocessing=False)

		for id in er.frame.index:
            result = er._get_result(id)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.error_bars_shrink(result, filename=filename_img)

            self.assertTrue(result['pass'])

	def run_recovers_original_densities(self):
		results_filename = 'recovers_original_densities_results'
	    dirname_prefix = 'recovers_original_densities'

		parser = recovers_original_densities.gen_parser()
	    args = parser.parse_args()

	    argsdict = eu.parser_args_to_dict(args)

		er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, 
			bucket_str='experiment_runner', storage_type='fs')

		er.do_experiments([argsdict], do_multiprocessing=False)

		for id in er.frame.index:
            result = er._get_result(id)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.plot_recovers_original_densities(result, filename=filename_img)

            self.assertTrue(result['pass']['sinwave'])
            self.assertTrue(result['pass']['x'])
            self.assertTrue(result['pass']['ring'])
            self.assertTrue(result['pass']['dots'])

	def run_haystacks_break(self):
		results_filename = 'haystacks_break_results'
	    dirname_prefix = 'haystacks_break'

		parser = haystacks_break.gen_parser()
	    args = parser.parse_args()

	    argsdict = eu.parser_args_to_dict(args)

		er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, 
			bucket_str='experiment_runner', storage_type='fs')

		er.do_experiments([argsdict], do_multiprocessing=False)

		for id in er.frame.index:
            result = er._get_result(id)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.plot_haystacks_break(result, filename=filename_img)

            self.assertTrue(result['pass'])

    def run_estimate_the_full_joint(self):
		results_filename = 'estimate_the_full_joint_results'
    	dirname_prefix = 'estimate_the_full_joint'

		parser = estimate_the_full_joint.gen_parser()
	    args = parser.parse_args()

	    argsdict = eu.parser_args_to_dict(args)

		er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, 
			bucket_str='experiment_runner', storage_type='fs')

		er.do_experiments([argsdict], do_multiprocessing=False)

		for id in er.frame.index:
            result = er._get_result(id)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.plot_estimate_the_full_joint(result, filename=filename_img)

            self.assertTrue(result['pass'])

    def run_fills_in_the_blanks(self):
		results_filename = 'fills_in_the_blanks_results'
    	dirname_prefix = 'fills_in_the_blanks'

		parser = fills_in_the_blanks.gen_parser()
	    args = parser.parse_args()

	    argsdict = eu.parser_args_to_dict(args)

		er = ExperimentRunner(run_experiment, dirname_prefix=dirname_prefix, 
			bucket_str='experiment_runner', storage_type='fs')

		er.do_experiments([argsdict], do_multiprocessing=False)

		for id in er.frame.index:
            result = er._get_result(id)
            this_dirname = eru._generate_dirname(dirname_prefix, 10, result['config'])
            filename_img = os.path.join(dirname_prefix, this_dirname, results_filename+'.png')
            eu.plot_fills_in_the_blanks(result, filename=filename_img)

            self.assertTrue(result['pass'])

if __name__ == '__main__':
	unittest.main()