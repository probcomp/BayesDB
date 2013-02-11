addpath ../matlab_code/

file_base = 'simple-anova';

data_file = strcat('../../data/',file_base,'-data');
label_file = strcat('../../data/',file_base,'-labels');
out_file = ['../../results/', file_base, + '-cc-results.csv'];

state = initialize_from_csv(data_file,...
    label_file, 'fromThePrior');

s = zeros(1000,state.F);

k = 0;
for i = 1:5
    
    state = analyze(state, {'columnPartitionHyperparameter',...
    'columnPartitionAssignments', 'componentHyperparameters',...
    'rowPartitionHyperparameters', 'rowPartitionAssignments'},...
    200, 'all', 'all');

    for j = 1:200
        
        k = k + 1;
        s(k,:) = simple_predictive_sample_newRow(state, [], 1:state.F);
    end
    
end

plot(s(:,1), s(:,2), '.')

figure 
hold all
for i = 1:100
   inds = state.o(1,:) == i;
   plot(state.data(inds, 1), state.data(inds, 2), '.')
end


