function run_crosscat(data_dir, file_base, experiment, n_pred_samples, ...
    n_mcmc_iter, seed, out_dir, out_file)
%
% run mutual information or conditional entropy experiment
%
% input:
%
% data_dir : directory that data is stored in, should include data/file_base-data.csv
%               and data/file_base-labels.csv
% file_base  : see data_dir
% experiment : either correlation to compute the mutual information for
%              each pair of columns or regression to compute
%              the conditional mutual information of the last variable
%              and each other predictor given the remaining predictor
% n_pred_samples : number of predictive samples to draw from each chain
% n_mcmc_iter    : number of mcmc steps to run each mcmc chain for
% seed           : random seed to use for this experiment
% out_dir        : where to print state file
% out_file : where to print model data probabilities and other output
%

if nargin < 8
    fid = 1;
else
    fid = fopen(out_file,'w');
end

rng(str2num(seed))

n_pred_samples = str2num(n_pred_samples);
n_mcmc_iter = str2num(n_mcmc_iter);

data_file = strcat(data_dir, file_base, '-data');
label_file = strcat(data_dir, file_base, '-labels');

state = initialize_from_csv(data_file, label_file, 'fromThePrior');

state = analyze(state, {'columnPartitionHyperparameter',...
    'columnPartitionAssignments', 'componentHyperparameters',...
    'rowPartitionHyperparameters', 'rowPartitionAssignments'},...
    n_mcmc_iter, 'all', 'all', false, fid);

name = [out_dir, file_base, '-', seed];
save(name, 'state');

switch experiment
    
    case 'correlation'
        
        h = cell(state.F, 1);
        for i = 2:state.F
            h{i} = zeros(i,1);
        end
        
        for k = 1:n_pred_samples
            
            s = simple_predictive_sample_newRow(state, [], 1:state.F);
            
            for i = 2:state.F
                for j = 1:(i - 1)
                    h{i}(j) = h{i}(j) + mutual_info(s, state, i, j, []);
                end
            end
            
        end
        
        for i = 2:state.F
            for j = 1:(i - 1)
                fprintf(fid, '#####%i,%i,%f#####\n', [i, j, h{i}(j)/n_pred_samples]);
            end
        end
        
    case 'regression'
        
        h_xz = 0;
        h_yz = 0;
        
        for j = 1:n_pred_samples
            
            s = simple_predictive_sample_newRow(state, [], 1:state.F);
            
            h_xz = h_xz + mutual_info(s, state, 1, 3, 2);
            h_yz = h_yz + mutual_info(s, state, 2, 3, 1);
        end
        
        fprintf(fid, 'I(Z,X|Y): #####%f#####\n', h_xz/n_pred_samples);
        fprintf(fid, 'I(Z,Y|X): #####%f#####\n', h_yz/n_pred_samples);
end

if fid ~= 1
    fclose(fid);
end
