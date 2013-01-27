function state = initialize_from_csv(dataFile, dataTypes, initialState)

    % BULID STATE
    % load data
    state.data = csvread([dataFile,'.csv']);
    fid = fopen([dataTypes, '.csv']);
    tmp = textscan(fid, '%s', 'Delimiter', ',');
    state.dataTypes = tmp{1};
    fclose(fid);
    
    state.F = size(state.data,2);
    state.O = size(state.data,1);
    
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
    state.crpPriorK = state.crpKRange(find(state.cumParamPrior>rand,1));
    state.crpPriorC = state.crpCRange(find(state.cumParamPrior>rand,1));
    
    % generate ranges for all dimensions
    for f = 1 : state.F
        switch state.dataTypes{f}

            case 'numeric'
                state = buildNumeric(state, f, bins);

            case 'binary'
                state = buildBinary(state, f, bins);
        end
    end

    % initialize state
    switch initialState
        case 'fromThePrior'
            state.f = sample_partition(state.F, state.crpPriorK);
            state.o = [];
            for i = 1 : max(state.f)
                state.crpPriorC(i) = state.crpCRange(find(state.cumParamPrior>rand,1));
                state.o(i,:) = sample_partition(state.O, state.crpPriorC(i));
            end
    
        case 'together'
            state.f = ones(1,state.F);
            state.o(1,:) = ones(1, state.O);
            
        case 'apart'
            state.f = 1 : state.F;
            for i = 1 : length(state.f)
                state.o(state.f(i),:) = 1:state.O;
                state.crpPriorC(i) = state.crpCRange(find(state.cumParamPrior>rand,1));
            end
            
        otherwise
            disp([initialState, ' is not a valid initialization option']);
            
    end
    
    % saveResults
    name = ['Samples/crossCat_', num2str(round(now*100000))];
    save(name, 'state');

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

    state.NG_a(f) = state.aRange(find(state.cumParamPrior>rand,1));
    state.NG_k(f) = state.kRange(find(state.cumParamPrior>rand,1));
    state.NG_b(f) = state.bRange(f,find(state.cumParamPrior>rand,1));

    state.NG_mu(f) = state.muRange(f,randi(length(state.muRange(f,:))));

end

function state = buildBinary(state, f, bins)
    
    % parameterized as strength and balance
    state.sRange = state.crpCRange;
    state.bRange = linspace(.03, .97, bins); % 0 to 1

    % sample values for strength and balance
    state.betaBern_s(f) = state.sRange(find(state.cumParamPrior>rand,1));
    state.betaBern_b(f) = state.bRange(find(state.cumParamPrior>rand,1));

end