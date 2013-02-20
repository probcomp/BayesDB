function run_crosscat(data_dir, file_base, experiment, n_pred_samples, ...
    n_mcmc_iter, seed)
%
% run mutual information or conditional entropy experiment
%
% input:
%
% file_base  : data set should be in files ../../data/file_base-data.csv
%              and ../../data/file_base-labels.csv
% experiment : either correlation to compute the mutual information for
%              each pair of columns or regression to compute
%              the conditional mutual information of the last variable
%              and each other predictor given the remaining predictor
% n_chains       : number of mcmc chains to draw samples from
% n_pred_samples : number of predictive samples to draw from each chain
% n_mcmc_iter    : number of mcmc steps to run each mcmc chain for
% seed           : random seed to use for this experiment
%

rng(str2num(seed))

n_pred_samples = str2num(n_pred_samples);
n_mcmc_iter = str2num(n_mcmc_iter);

data_file = strcat(data_dir, file_base, '-data');
label_file = strcat(data_dir, file_base, '-labels');

state = initialize_from_csv(data_file, label_file, 'fromThePrior');

state = analyze(state, {'columnPartitionHyperparameter',...
    'columnPartitionAssignments', 'componentHyperparameters',...
    'rowPartitionHyperparameters', 'rowPartitionAssignments'},...
    n_mcmc_iter, 'all', 'all');

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
                fprintf(1, '#####%i,%i,%f#####\n', [i, j, h{i}(j)/n_pred_samples]);
            end
        end
        
    case 'regression'
        
        pi_x_y = 0;      
        mi_x = 0;
        mi_y = 0;
        mi_xy = 0;
        
        for j = 1:n_pred_samples
            
            s = simple_predictive_sample_newRow(state, [], 1:state.F);
            
            pi_x_y = partial_info(s, state, 3, 1, 2, n_pred_samples);
            mi_x = m_x + mutual_info(s, state, 1, 3, []);
            mi_y = m_y + mutual_info(s, state, 2, 3, []);
            mi_xy = mi_xy + mutual_info(s, state, [1,2], 3, []);
        end
        
        pi_x_y = pi_x_y/n_pred_samples;
        mi_x = mi_x/n_pred_samples;
        mi_y = mi_y/n_pred_samples;
        mi_xy = mi_xy/n_pred_samples;
        
        pi_x = mi_x - pi_x_y;
        pi_y = mi_y - pi_x_y;
        pi_xy = mi_xy - pi_x - pi_y - pi_x_y;
        
        fprintf(1, 'Pi({X}): #####%f#####\n', pi_x);
        fprintf(1, 'Pi({Y}): #####%f#####\n', pi_y);
        fprintf(1, 'Pi({X}{Y}): #####%f#####\n', pi_x_y);
        fprintf(1, 'Pi({X,Y}): #####%f#####\n', pi_xy);
        
end

