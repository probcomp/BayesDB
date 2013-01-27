function state = initialize_from_json(filename)

    fid = fopen(filename);
    S = fscanf(fid, '%s');
    fclose(fid);

    idx = strfind(S, '"idx_to_name"');
    closedBracket = strfind(S, '}');

    for i = length(idx):-1:1
        starting = idx(i)-1;
        ending = find(idx(i)<closedBracket,1);
        S = S([1:starting-1, closedBracket(ending)+1:end]);
    end

    idx = strfind(S, '"value_to_code"');
    closedBracket = strfind(S, '}');

    for i = length(idx):-1:1
        starting = idx(i)-1;
        ending = find(idx(i)<closedBracket,1);
        S = S([1:starting-1, closedBracket(ending)+1:end]);
    end
    
    S = strrep(S, '1_count', 'one_count');
    S = strrep(S, '0_count', 'zero_count');
    
    datastruct = JSON.load(S);
    
    state.data = datastruct.T.data;
    state.O = datastruct.T.dimensions(1);
    state.F = datastruct.T.dimensions(2);
    state.f = datastruct.X_L.column_partition.assignments+1;
    uf = unique(state.f);
    for i = 1 : length(uf)
        state.o(uf(i),:) = datastruct.X_D(uf(i),:)+1;
        state.crpPriorC(uf(i)) = exp(datastruct.X_L.view_state(i).row_partition_model.hypers.log_alpha);
    end
    state.crpPriorK = exp(datastruct.X_L.column_partition.hypers.log_alpha);
    %state.dataTypes
    for i = 1 : state.F
        state.dataTypes{i} = datastruct.M_c.column_metadata(i).modeltype;
    end
    
    % parameters
    bins = 31; % must be odd

    %Parameter priors are assumed to be uniform in this version
    state.paramPrior = ones(1,bins); % uniform prior on parameters
    state.paramPrior = state.paramPrior ./ sum(state.paramPrior);
    state.cumParamPrior = cumsum(state.paramPrior);
    
    % CRP parameters
    state.crpKRange = exp(linspace(log(1/state.F), log(state.F), bins));
    state.crpCRange = exp(linspace(log(1/state.O), log(state.O), bins));

    % sample values
    if isempty(state.crpPriorK)
        state.crpPriorK = state.crpKRange(find(state.cumParamPrior>rand,1));
    end
    
    if isempty(state.crpPriorC)
        uc = unique(state.f);
        for i = uc
            state.crpPriorC(i) = state.crpCRange(find(state.cumParamPrior>rand,1));
        end
    end
    
    % do hyperparameters and ranges
    % generate ranges for all dimensions
    for f = 1 : state.F
        switch state.dataTypes{f}

            case 'normal_inverse_gamma'
                state.NG_a(f) = exp(datastruct.X_L.column_hypers(f).log_alpha);
                state.NG_k(f) = exp(datastruct.X_L.column_hypers(f).log_kappa);
                state.NG_b(f) = exp(datastruct.X_L.column_hypers(f).log_beta);
                state.NG_mu(f) = datastruct.X_L.column_hypers(f).mu;
                state = buildNumeric(state, f, bins);

            case 'asymmetric_beta_bernoulli'
                state.betaBern_b(f) = datastruct.X_L.column_hypers(f).balance;
                state.betaBern_s(f) = exp(datastruct.X_L.column_hypers(f).log_strength);
                state = buildBinary(state, f, bins);
        end
    end
    
end

function state = buildNumeric(state, f, bins)
    
    % set k parameter range
    state.kRange = state.crpCRange;
    % set a range to n/2
    state.aRange = exp(linspace(log(1/(state.O/2)), log(state.O/2), bins));
    
    % set mu and beta ranges
    notNan = state.data(~isnan(state.data(:,f)), f);
    if length(notNan)==1 % use all continuous data, here all data
        notNan = state.data(~isnan(state.data));
    end
    
    % mu
    state.muRange(f,:) = linspace(min(state.data(:,f)),max(state.data(:,f)),30); % uniform prior
    
    % set b max based on max empirical SSD
    ssd = sum((notNan-mean(notNan)).^2);
    % NOTE: assumes ssd is greater than 1!
    state.bRange(f,:) = exp(linspace(log(1/ssd), log(ssd), bins));
    % NOTE: all parameter ranges are set based on sufficient stats, such
    % that the max of the range is equal to the max possible from the data
    % we assume a common range for all features

    if isempty(state.NG_a(f))
        state.NG_a(f) = state.aRange(find(state.cumParamPrior>rand,1));
    end
    
    if isempty(state.NG_k(f))
        state.NG_k(f) = state.kRange(find(state.cumParamPrior>rand,1));
    end
    
    if isempty(state.NG_B(f))
        state.NG_b(f) = state.bRange(f,find(state.cumParamPrior>rand,1));
    end
    
    if isempty(state.NG_mu(f))
        state.NG_mu(f) = state.muRange(f,randi(length(state.muRange(f,:))));
    end
end

function state = buildBinary(state, f, bins)
    
    % parameterized as strength and balance
    state.sRange = state.crpCRange;
    state.bRange = linspace(.03, .97, bins); % 0 to 1

    % sample values for strength and balance if empty
    if isempty(state.betaBern_s(f))
        state.betaBern_s(f) = state.sRange(find(state.cumParamPrior>rand,1));
    end
    
    if isempty(state.betaBern_b(f))
        state.betaBern_b(f) = state.bRange(find(state.cumParamPrior>rand,1));
    end
    
end