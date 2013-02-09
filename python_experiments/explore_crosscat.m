addpath ../matlab_code/

file_base = 'ring-width-0.5'

data_file = strcat('../../data/',file_base,'-data');
label_file = strcat('../../data/',file_base,'-labels');
out_file = ['../../results/', file_base, + '-cc-results.csv'];

state = initialize_from_csv(data_file,...
    label_file, 'fromThePrior');

state = analyze(state, {'columnPartitionHyperparameter',...
    'columnPartitionAssignments', 'componentHyperparameters',...
    'rowPartitionHyperparameters', 'rowPartitionAssignments'},...
    10, 'all', 'all');

s = zeros(1000,2);
h = zeros(1000,2);

for i = 1:1000

s(i,:) = simple_predictive_sample_newRow(state, [], [1 2]);

end

plot(s(:,1), s(:,2), '.')

figure 
hold all
for i = 1:100
   inds = state.o(1,:) == i;
   plot(state.data(inds, 1), state.data(inds, 2), '.')
end


