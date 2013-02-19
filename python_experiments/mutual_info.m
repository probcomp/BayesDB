function h = mutual_info(sample, state, x_var, y_var, given_vars)
%
% approximate I(X, Y | Z)
%
% input:
%
% state          : an initial crosscat state, e.g. from initialize_from_csv
% x_var          : a column index for X (first variable)
% y_var          : a column index for Y (second variable)
% given_vars     : a vector of column indices for Z (conditioning variables)
%

Y = struct('indices', given_vars, 'values', sample(given_vars));
Q = struct('indices', y_var, 'values', sample(y_var));
p_y = simple_predictive_probability_newRows(state, Y, Q);

Y = struct('indices', [given_vars, x_var], 'values', sample([given_vars, x_var]));
Q = struct('indices', y_var, 'values', sample(y_var));
p_conditional = simple_predictive_probability_newRows(state, Y, Q);

% I(X, Y | Z) = H(Y | Z) - H(Y | X, Z)
%   = E[ -log(y | z) + log(y | x, y) ]
%   = E[ log(y | x, z) - log(y | z) ]
h = log(p_conditional) - log(p_y);