function h = partial_info(sample, state, z_var, x_var, y_var, ...
    n_pred_samples)
%
% approximate Imin(Z;{X}{Y}) = E_z[ min( I(Z = z,X), I(Z = z, Y) )]
%
% input:
%
% state          : an initial crosscat state, e.g. from initialize_from_csv
% x_var          : a column index for X (first variable)
% y_var          : a column index for Y (second variable)
% given_vars     : a vector of column indices for Z (conditioning variables)
%


pmi = zeros(1,2);

Y = [z_var, sample(z_var)];

for i = 1:n_pred_samples
    
    sample(x_var) = simple_predictive_sample_newRow(state, Y, x_var);
    pmi(1) = pmi(1) + mutual_info(sample, state, z_var, x_var, []);
    
    sample(y_var) = simple_predictive_sample_newRow(state, Y, y_var);
    pmi(2) = pmi(2) + mutual_info(sample, state, z_var, y_var, []);
    
end

pmi = pmi/n_pred_samples;

h = min(pmi);
