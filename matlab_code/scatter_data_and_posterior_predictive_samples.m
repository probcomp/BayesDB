function scatter_data_and_posterior_predictive_samples(state)
    % assumes 2D

    for i = 1 : state.O
        samples(i,:) = simple_predictive_sample_newRow(state, [], [1 2]);
    end

    scatter(state.data(:,1), state.data(:,2), 'b');
    hold on;
    scatter(samples(:,1), samples(:,2), 'r');

end