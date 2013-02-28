function samples = simple_predictive_sample(state, Y, q)
    % Y is a struct with two fields. the indices field contains a n x 2 list of
    % condition variables. the values field contains an n x 1 list of values. if an
    % observed cell is listed, the old value is ignored.
    % q is a cell array, where each cell contains a struct with two fields:
    % indices and dataTypes. indices is a [row column] and dataTypes is a
    % data type.
    % in the data table (new row and new column must be treated correctly).
    % if an observed cell is listed, then the observed value is ignored.
    % NOTE: the values in Y must be of the appropriate type!
    
    samples = zeros(size(q,1),1);
    
    if isempty(Y)
        Y.indices = [];
        Y.values = [];
    end
    
    % cycle through q
    for i = 1 : size(q,1)
        
        % four possibilities
        if q{i}.indices(2) <= state.F && q{i}.indices(1) <= state.O % old column, old row 
            
            % find the relevant view and category
            thisView = state.f(q{i}.indices(2));
            thisCategory = state.o(thisView,q{i}.indices(1));
            
            % find the relevant data
            theseRows = state.o(thisView,:)==thisCategory;
            theseData = state.data(theseRows,q{i}.indices(2));
            
            % sample a value based on the observed values in that column (depends on
            % datatype)
            samples(i) = sampleValue(theseData, q{i}, state);
            
        elseif q{i}.indices(2) <= state.F && q{i}.indices(1) > state.O % old column, new row 
            
            % find the relevant view
            thisView = state.f(q{i}.indices(2));
            
            % sample a category based on the conditions (observations of
            % this row with columns in this view)
            thisCategory = chooseCategoryGivenView(state, Y, q{i}, thisView);
            
            % sample this value based on the observed values in that column
            % & category
            
            % get data for this category
            theseRows = state.o(thisView,:)==thisCategory;
            theseRows = theseRows' & ~isnan(state.data(:,q{i}.indices(2)));
            theseData = state.data(theseRows,q{i}.indices(2));

            % sample a value based on the observed values in that column (depends on
            % datatype)
            samples(i) = sampleValue(theseData, q{i}, state);
            
        elseif q{i}.indices(2) > state.F && q{i}.indices(1) <= state.O % new column, old row
            
            % choose view based on conditions (observations of this column
            % and old rows)
            thisView = sampleView(state, Y, q{i}); 
            
            tmpState = state;
            tmpState.F = state.F+1;
            tmpState.f(tmpState.F) = thisView;
            tmpState.data(:,end+1) = NaN;
            tmpState.crpPriorC(state.F) = find(state.cumParamPrior>rand,1);
            tmpState.dataTypes{tmpState.F} = q{i}.dataTypes;
            % sample parameters based on dataType
            switch q{i}.dataTypes
                case 'normal_inverse_gamma'
                        tmpState = buildNumeric(tmpState, tmpState.F, 31);

                case 'asymmetric_beta_bernoulli'
                        tmpState = buildBinary(tmpState, tmpState.F, 31);
            end
                
            % two possibilties: old view & new view
            if thisView == state.F+1
                % new view
                % means that we need to sample a categorization (run gibbs
                % sampler on values in conditions), then sample a value based
                % on the categorization
                                
                % get the relevant data
                if ~isempty(Y.indices)
                    theseData = Y.indices(:,2)==q{i}.indices(2);
                    tmpState.data(theseData) = Y.values(theseData);
                end

                % run gibbs sampler
                tmpState.o(thisView,:) = sample_partition(state.O, tmpState.crpPriorC(state.F));
                tmpState = analyze(tmpState, ...
                    {'componentHyperparameters', 'rowPartitionAssignments'}, ...
                    2, state.F, []);
                thisCategory = tmpState.o(thisView,q{i}.indices(1));
                
                % get data for this category
                theseRows = tmpState.o(thisView,:)==thisCategory;
                theseRows = theseRows' & ~isnan(tmpState.data(theseRows,tmpState.F));
                theseData = tmpState.data(theseRows,q{i}.indices(2));

                % sample a value based on the observed values in that column (depends on
                % datatype)
                samples(i) = sampleValue(theseData, q{i}, tmpState);
                
            else
                % old view 
                % means that we have a category, need to sample a
                % value based on observed cells in conditions (this feature,
                % rows in this category)
                thisCategory = tmpState.o(thisView,q{i}.indices(1));
                
                % find the relevant data
                theseRows = tmpState.o(thisView,:)==thisCategory;
                theseRows = theseRows' & ~isnan(tmpState.data(:,tmpState.F));
                theseData = tmpState.data(theseRows,q{i}.indices(2));
                                
                % sample a value based on the observed values in that column (depends on
                % datatype)
                samples(i) = sampleValue(theseData, q{i}, tmpState);
                
            end
            
        elseif q{i}.indices(2) > state.F && q{i}.indices(1) > state.O % new column, new row
            
            % choose view based on conditions (observations of this column
            % and old rows)
            thisView = sampleView(state, Y, q{i}); 
            
            tmpState = state;
            tmpState.F = state.F+1;
            tmpState.O = state.O+1;
            tmpState.f(tmpState.F) = thisView;
            tmpState.data(:,end+1) = NaN;
            tmpState.data(end+1,:) = NaN;
            tmpState.crpPriorC(state.F) = find(state.cumParamPrior>rand,1);
            tmpState.dataTypes{state.F} = q{i}.dataTypes;
            
            % sample parameters based on dataType
            switch q{i}.dataTypes
                case 'normal_inverse_gamma'
                        tmpState = buildNumeric(tmpState, tmpState.F, 31);

                case 'asymmetric_beta_bernoulli'
                        tmpState = buildBinary(tmpState, tmpState.F, 31);
            end
            
            % two possibilties: old view & new view
            if thisView == state.F+1
                % new view
                % means that we need to sample a categorization (run gibbs
                % sampler on values in conditions), then sample a value based
                % on the categorization
                
                if ~isempty(Y.indices)
                    theseData = Y.indices(:,2)==q{i}.indices(2);
                    tmpState.data(theseData) = Y.values(theseData);
                end
                
                % run gibbs sampler
                tmpState.o(:,end+1) = 0;
                tmpState.o(thisView,:) = sample_partition(tmpState.O, tmpState.crpPriorC(state.F));
                           
                tmpState = analyze(tmpState, ...
                    {'componentHyperparameters', 'rowPartitionAssignments'}, ...
                    2, state.F, []);
                
                thisCategory = tmpState.o(thisView,q{i}.indices(1));
                
                % get data for this category
                theseRows = tmpState.o(thisView,:)==thisCategory;
                theseRows = theseRows' & ~isnan(tmpState.data(:,tmpState.F));
                theseData = tmpState.data(theseRows,q{i}.indices(2));

                % sample a value based on the observed values in that column (depends on
                % datatype)
                samples(i) = sampleValue(theseData, q{i}, tmpState);
                
            else
                % old view 
                
                % sample a category based on the conditions (observations of
                % this row with columns in this view)
                thisCategory = chooseCategoryGivenView(tmpState, Y, q{i}, thisView);

                % sample this value based on the observed values in that column
                % & category
                
                % get data for this category
                theseRows = state.o(thisView,:)==thisCategory;
                theseRows = theseRows' & ~isnan(tmpState.data(1:end-1,tmpState.F));
                theseRows(end+1) = 0;
                theseData = tmpState.data(theseRows,q{i}.indices(2));

                % sample a value based on the observed values in that column (depends on
                % datatype)
                samples(i) = sampleValue(theseData, q{i}, tmpState);

            end
            
        end
        
    end
    

end

function sample = sample_beta_bernoulli(sum0, sum1)
    prob = [ sum0./(sum0+sum1), sum1./(sum0+sum1) ];
    cumProb = cumsum(prob);          
    sample = find(rand<cumProb,1)-1;
end

function s = logsumexp(a, dim)
    % Returns log(sum(exp(a),dim)) while avoiding numerical underflow.
    % Default is dim = 1 (rows) or dim=2 for a row vector
    % logsumexp(a, 2) will sum across columns instead of rows

    % Written by Tom Minka, modified by Kevin Murphy

    if nargin < 2
      dim = 1;
      if ndims(a) <= 2 & size(a,1)==1
        dim = 2;
      end
    end

    % subtract the largest in each column
    [y, i] = max(a,[],dim);
    dims = ones(1,ndims(a));
    dims(dim) = size(a,dim);
    a = a - repmat(y, dims);
    s = y + log(sum(exp(a),dim));
end

function logProb = NG_cat(data, newData, mu0, k0, a0, b0)
    % this is based on kevin murphy's cheat sheet (NG.pdf)
    % data are assumed to be a vector
    % mu0, k0, a0, b0 are hyperparameters
    % NOTE: this version is for the gibbs sampler for categories
    
    % NOTE: deal with missing data by removing NaNs
    data = data(~isnan(data));
    newData = newData(~isnan(newData));
    
    % check that there are new data to consider
    if isempty(newData)
        logProb = 0;
        return
    end
    
    % this is updating based on old data
    if isempty(data)
        % do nothing
    else
        % NOTE: this could be cached
        len = length(data);
        meanData = sum(data,1)/len;
        
        mu0 = (k0.*mu0 + len.*meanData) ./ (k0+len);
        k0 = k0+len; 
        a0 = a0 + len./2;

        diff1 = data-meanData;
        diff2 = meanData-mu0;
        b0 = b0 + .5 .* sum( diff1.*diff1 ) + ...
                          (k0.*len.*(diff2.*diff2) ) ./ ...
                           (2.*(k0+len));
    end
    
    len = length(newData);
    meanData = sum(newData,1)/len;
    
    % now update with new data
    %muN = (k0.*mu0 + len.*meanData) ./ (k0+len);
    kN = k0+len;
    aN = a0 + len./2;

    diff1 = newData-meanData;
    diff2 = meanData-mu0;
    bN = b0 + .5 .* sum( diff1.*diff1 ) + ...
                          (k0.*len.*(diff2.*diff2) ) ./ ...
                           (2.*(k0+len));
    
    logProb = gammaln(aN)-gammaln(a0) + ...
           log(b0).*a0 - log(bN).*aN + ...
           log( (k0./kN) ).*.5  + ...
           log( (2*pi) ).*(-len/2);
end

function sample = sampleValue(theseData, q, state)

    switch q.dataTypes
        case 'asymmetric_beta_bernoulli'

            sum1 = sum(theseData==1) + state.betaBern_s(q.indices(2)) .* state.betaBern_b(q.indices(2));
            sum0 = sum(theseData==0) + state.betaBern_s(q.indices(2)) .* (1 - state.betaBern_b(q.indices(2)));
            sample = sample_beta_bernoulli(sum0, sum1);

        case 'dirichlet_multinomal'

            % FIXME

        case 'normal_inverse_gamma'

            % sample from posterior predictive distribution
            len1 = length(theseData);
            meanData = mean(theseData);
            
            b0 = state.NG_b(q.indices(2));
            a0 = state.NG_a(q.indices(2));
            k0 = state.NG_k(q.indices(2));
            mu0 = state.NG_mu(q.indices(2));
            
            if len1 > 0
                aN = a0 + len1./2;
                kN = k0 + len1;
                muN = (k0.*mu0 + len1.*meanData) ./ (k0+len1);
                bN = b0 + .5 .* sum( (theseData-repmat(meanData,size(theseData,1),1)).^2,1) + ...
                                  (k0.*len1.*(meanData-mu0).^2 ) ./ ...
                                   (2.*(k0(1)+len1));
            else
                aN = a0;
                kN = k0;
                bN = b0;
                muN = mu0;
            end
            sample = trnd(2.*aN) .* sqrt((bN.*(kN+1))./(aN.*kN)) + muN;
    end
end

function thisCategory = chooseCategoryGivenView(state, Y, q, thisView)
    % column in this view
    columnsInView = find(state.f==thisView);
    relevantColumns = ~ones(size(Y.indices,1),1);
    if ~isempty(relevantColumns)
        for ii = 1 : length(columnsInView)
            relevantColumns = relevantColumns || (Y.indices(:,2)==columnsInView(ii));
        end
        relevantConditions = find(relevantColumns && (Y.indices(:,1)==q.indices(1)));
    else
        relevantConditions = find(relevantColumns);
    end
    
    
    % compute counts
    uc = unique(state.o(state.f(q.indices(2)),:));
    uc(end+1) = state.O+1; % allow possibility of new category
    counts = zeros(1, length(uc));

    logProb = zeros(1,length(uc));
    for ii = 1 : length(uc)

        % count number of rows in category
        theseRows = state.o(thisView,:)==uc(ii);
        counts(ii) = sum(theseRows);

        if ~isempty(relevantConditions)

            % cycle over features scoring probabilty of these values
            % given this category

            for iii = 1 : length(relevantConditions)
                tmpColumn = Y.indices(relevantConditions(iii),2);
                theseData = state.data(theseRows, tmpColumn); 

                switch state.dataTypes{Y.indices(relevantConditions(iii),2)}

                    case 'asymmetric_beta_bernoulli'
                        thisValue = zeros(1,2);
                        thisValue(Y.values(relevantConditions(iii))+1) = 1;
                        sum1 = thisValue(2) + sum(theseData==1) + state.betaBern_s(tmpColumn) .* state.betaBern_b(tmpColumn);
                        sum0 = thisValue(1) + sum(theseData==0) + state.betaBern_s(tmpColumn) .* (1 - state.betaBern_b(tmpColumn));
                        tmpProb = normalize([sum0, sum1]);
                        logProb(ii) = logProb(ii)+ log( tmpProb(Y.values(relevantConditions(iii))+1) );

                    case 'dirichlet_multinomial'
                        % FIXME

                    case 'normal_inverse_gamma'
                        logProb(ii) = logProb(ii) + ...
                            NG_cat(theseData, Y.values(relevantConditions(iii)), ...
                            state.NG_mu(tmpColumn), state.NG_k(tmpColumn), ...
                            state.NG_a(tmpColumn), state.NG_b(tmpColumn));
                end
            end
        end

        % add in CRP prob
        if ii < length(uc)
            logProb(ii) = logProb(ii) + ...
                log(counts(ii)/(state.O+state.crpPriorC(thisView)));      
        else
            logProb(ii) = logProb(ii) + ...
                log(state.crpPriorC(thisView) / (state.O+state.crpPriorC(thisView)));
        end
    end

    % choose a category
    logProb = logProb - logsumexp(logProb);
    cumProb = cumsum(exp(logProb));
    thisCategory = find(cumProb > rand, 1);
    thisCategory = uc(thisCategory);

end

function thisView = sampleView(state, Y, q)
    
    % find conditions that correspond to this query
    if ~isempty(Y.indices)
        theseData = Y.indices(:,2) == q.indices(2);
        rows = Y.indices(theseData,1);
    else
       theseData = [];
       rows = [];
    end
    
    % pull out their values
    theseData = Y.values(theseData);
    data = ones(state.O,1);
    data(data==1) = NaN;
    
    tmpState = state;
    tmpState.data(:,end+1) = data;
    tmpState.F = state.F+1;
    tmpState.dataTypes{tmpState.F} = q.dataTypes;
    tmpState.crpPriorC = state.crpCRange(find(state.cumParamPrior>rand,1));
    tmpState.o(tmpState.F,:) = sample_partition(tmpState.O, tmpState.crpPriorC);
    
    % sample parameters based on dataType
    switch q.dataTypes
        case 'normal_inverse_gamma'
                tmpState = buildNumeric(tmpState, tmpState.F, 31);

        case 'asymmetric_beta_bernoulli'
                tmpState = buildBinary(tmpState, tmpState.F, 31);
    end
        
    % score column on different views
    uv = unique(state.f);
    for i = 1 : length(uv)
        tmpState.f(tmpState.F) = uv(i);
        logP(i) = sum(state.f==uv(i))./(state.F+tmpState.crpPriorK);
        logP(i) = logP(i) + scoreFeature(tmpState, tmpState.F);
    end
    % score new view
    uv(end+1) = tmpState.F;
    logP(end+1) = tmpState.crpPriorK ./ (state.F+tmpState.crpPriorK);
    
    % choose probabilistically
    prob = exp(logP - logsumexp(logP));
    cumProb = cumsum(prob);
    thisView = uv(find(cumProb > rand,1));
    
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
    if ~isnan(min(state.data(:,f)))
        state.muRange(f,:) = linspace(min(state.data(:,f)),max(state.data(:,f)),30); % uniform prior
    else
        % if only a single value, set based on all data
        state.muRange(f,:) = linspace(min(state.data(:)),max(state.data(:)),30);
    end
    
    % set b max based on max empirical SSD
    ssd = sum((notNan-mean(notNan)).^2);
    
    if ssd ~=0
        % NOTE: assumes ssd is greater than 1!
        state.bRange(f,:) = exp(linspace(log(1/ssd), log(ssd), bins));
    else
        % if there is only a single value, set based on other data
        state.bRange(f,:) = exp(linspace(log(1/max(state.bRange(:))), log(max(state.bRange(:))), bins));
    end
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

function logP = scoreFeature(state,f)
    % score feature
    K = state.f(f);
    c = unique(state.o(K,:));
    logP = 0;
    for j = c
        theseData = state.o(K,:)==j;
        switch state.dataTypes{f}
            case 'normal_inverse_gamma'
                logP = logP + NG(state.data(theseData,f), ...
                               state.NG_mu(f), state.NG_k(f), ...
                               state.NG_a(f), state.NG_b(f));
            case 'dirichlet_multinomial '
                % FIXME
                disp('FIXME!');
            case 'asymmetric_beta_bernoulli '
                logP = logP + betaBern(state.data(theseData,f), ...
                                        state.betaBern_s(f), ...
                                        state.betaBern_b(f));
        end
    end
end

function logProb = betaBern(data, strength, balance)
    
    numTrue = sum(data);
    numFalse = length(data)-numTrue;
    
    fakeTrue = strength*balance;
    fakeFalse = strength*(1-balance);
    
    logProb = betaln(numTrue+fakeTrue, numFalse+fakeFalse) - ...
              betaln(fakeTrue, fakeFalse);
    
end

function logProb = NG(data, mu0, k0, a0, b0)
    % this is based on kevin murphy's cheat sheet (NG.pdf)
    % data are assumed to be a vector
    % mu0, k0, a0, b0 are hyperparameters

    % NOTE: deal with missing data by removing NaNs
    data = data(~isnan(data));
    % check if there are data
    if isempty(data)
        logProb = 0;
        return
    end
    
    len = length(data);
    meanData = sum(data,1)/len;
    
%     muN = (k0.*mu0 + len.*meanData) ./ (k0+len);
    kN = k0+len;
    aN = a0 + len./2;

    diff1 = data-meanData;
    diff2 = meanData-mu0;
    bN = b0 + .5 .* sum( diff1.*diff1 ) + ...
                          (k0.*len.*(diff2.*diff2)) ./ ...
                           (2.*(k0+len));


    logProb = gammaln(aN)-gammaln(a0) + ...
           log(b0).*a0 - log(bN).*aN + ...
           log( (k0./kN) ) .*.5 + ...
           log( (2*pi) ).*(-len/2);
       
end

function [partition] = sample_partition(n, gama)
% this samples category partions given # objects from crp prior

partition = ones(1,n);
classes = [1,0];

    for i=2:n
      classprobs=[];

      for j=1:length(classes)

        if classes(j) > 0.5
          classprobs(j) = (classes(j))./(i-1+gama);
        else
          classprobs(j) = gama./(i-1+gama);
        end

      end

      cumclassprobs = cumsum(classprobs);
      c = min(find(rand<cumclassprobs));
      partition(i) = c;
      classes(c)=classes(c)+1;

      % if we add new class, need to replace placeholder

      if c==length(classes)
        classes(c+1)=0;
      end

    end
end
