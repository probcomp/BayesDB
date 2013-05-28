#!python
import argparse
import jenkinsapi.jenkins
import jenkinsapi.job


def get_existing_config(fullurl):
	jenkins_obj = jenkinsapi.jenkins.Jenkins(fullurl)
	jenkins_job = jenkinsapi.job.Job(fullurl, '', jenkins_obj)
	config = jenkins_job.get_config()
	return config

def create_jenkins_job(baseurl, job_name, config):
	jenkins_obj = jenkinsapi.jenkins.Jenkins(baseurl)
	jenkins_obj.create_job(job_name, config)
	return None

def read_file(config_filename):
	config = None
	with open(config_filename) as fh:
		config = ''.join(line for line in fh)
	return config

def write_file(config, config_filename):
	with open(config_filename, 'w') as fh:
		fh.write(config)
	return


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--baseurl', default='http://localhost:8080', type=str)
	parser.add_argument('--job_name', default='PredictiveDB', type=str)
	parser.add_argument('--config_filename', default='config.xml', type=str)
	parser.add_argument('-get', action='store_true')
	#
	args = parser.parse_args()
	baseurl = args.baseurl
	job_name = args.job_name
	config_filename = args.config_filename
	do_get = args.get
	#
	if do_get:
		fullurl = '%s/job/%s' % (baseurl, job_name)
		config = get_existing_config(fullurl)
		write_file(config, config_filename)
	else:
		config = read_file(config_filename)
		create_jenkins_job(baseurl, job_name, config)

