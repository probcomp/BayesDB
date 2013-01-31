function run_crosscat(file_base)

data_file = strcat('../../data/',file_base,'-data');
label_file = strcat('../../data/',file_base,'-labels');

state = initialize_from_csv(data_file,...
    label_file, 'together');

state = analyze(state, {'columnPartitionHyperparameter',...
    'columnPartitionAssignments', 'componentHyperparameters',...
    'rowPartitionHyperparameters', 'rowPartitionAssignments'},...
    100, 'all', 'all',[],[]);

out_file = '../../results/' + file_base + '-cc-results.csv';

s = zeros(1000,2);
h = zeros(1000,2);

for i = 1:1000
    
q = cell(2,1);
for f = 1:state.F
    q{f} = struct('indices', [state.O + 1, f], 'dataTypes', 'normal_inverse_gamma');
end

x = simple_predictive_sample(state, [], q);

s(i,:) = x;
h(i,:) = log(p/jointp);

end

plot(s(:,1), s(:,2), '.')

save(out_file, state, q)



