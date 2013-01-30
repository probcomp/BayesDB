function run_crosscat(file_base)

addpath ../matlab_code/

data_file = '../../data/' + file_base + '-data.csv';
label_file = '../../data/' + file_base + '-labels.csv';

state = initialize_from_csv(data_file,...
    label_file, 'together');

state = analyze(state, {'columnPartitionHyperparameter',...
    'columnPartitionAssignments', 'componentHyperparameters',...
    'rowPartitionHyperparameters', 'rowPartitionAssignments'},...
    100, 'all', 'all',[],[]);

out_file = '../../results/' + file_base + '-cc-results.csv';

save(out_file, state)



