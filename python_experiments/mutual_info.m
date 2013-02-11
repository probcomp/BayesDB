function h = mutual_info(state, x_var, y_var, given_vars, ...
    n_chains, n_pred_samples, n_mcmc_iter)
%
% approximate I(X, Y | Z) using n_chains*n_pred_samples predictive samples
%
% input:
%
% state          : an initial crosscat state, e.g. from initialize_from_csv
% x_var          : a column index for X (first variable)
% y_var          : a column index for Y (second variable)
% given_vars     : a vector of column indices for Z (conditioning variables)
% n_chains       : number of mcmc chains to draw samples from
% n_pred_samples : number of predictive samples to draw from each chain
% n_mcmc_iter    : number of mcmc steps to run each mcmc chain for
%

n = n_chains*n_pred_samples;

h = 0;

for i = 1:n_chains
    
    state = analyze(state, {'columnPartitionHyperparameter',...
        'columnPartitionAssignments', 'componentHyperparameters',...
        'rowPartitionHyperparameters', 'rowPartitionAssignments'},...
        n_mcmc_iter, 'all', 'all');

    for j = 1:n_pred_samples
            
        s = simple_predictive_sample_newRow(state, [], 1:state.F);
        
        Y = struct('indices', given_vars, 'values', s(given_vars));
        Q = struct('indices', y_var, 'values', s(y_var));
        p_y = simple_predictive_probability_newRows(state, Y, Q);
        
        Y = struct('indices', [given_vars, x_var], 'values', s([given_vars, x_var]));
        Q = struct('indices', y_var, 'values', s(y_var));     
        p_conditional = simple_predictive_probability_newRows(state, Y, Q);
        
        % I(X, Y | Z) = H(Y | Z) - H(Y | X, Z)
        %   = E[ -log(y | z) + log(y | x, y) ]
        %   = E[ log(y | x, z) - log(y | z) ]
        h = h + log(p_conditional) - log(p_y);
    
    end
end

h = h/n;
