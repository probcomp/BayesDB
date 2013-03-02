addpath ../matlab_code/

%file_base = 'ring-i-0-width-0.3-missing';
file_base = 'correlated-pairs-i-0-n-100-corr-0.6';

data_file = strcat('../../data/',file_base,'-data');
label_file = strcat('../../data/',file_base,'-labels');
out_file = ['../../results/', file_base, + '-cc-results.csv'];

state = initialize_from_csv(data_file,...
    label_file, 'apart');

state = analyze(state, {'columnPartitionHyperparameter',...
    'columnPartitionAssignments', 'componentHyperparameters',...
    'rowPartitionHyperparameters', 'rowPartitionAssignments'},...
    500, 'all', 'all');

s = zeros(200,state.F);


for j = 1:200
    
    k = k + 1;
    s(k,:) = simple_predictive_sample_newRow(state, [], 1:state.F);
end

figure
hold all

plot(s(:,1), s(:,2), 'x')

for i = 1:100
    inds = state.o(1,:) == i;
    plot(state.data(inds, 1), state.data(inds, 2), '.')
end


