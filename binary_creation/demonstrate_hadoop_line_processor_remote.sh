python xnet_utils.py pickle_table_data
python xnet_utils.py write_initialization_files --n_chains 20
cp initialize_input hadoop_input
bash send_hadoop_command.sh
cp myOutputDir/part-00000 initialize_output
python xnet_utils.py link_initialize_to_analyze --initialize_input_filename myOutputDir/part-00000 --n_steps 20
cp analyze_input hadoop_input
bash send_hadoop_command.sh
cp myOutputDir/part-00000 analyze_output
