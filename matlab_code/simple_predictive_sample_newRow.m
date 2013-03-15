function sample = simple_predictive_sample_newRow(state, Y, q)
    % this works on a single query. 
    % Y is a condition x [index value] matrix
    % q is a vector of column indices being queried

    % create observed row
    newRow = ones(1,state.F);
    newRow(newRow==1) = NaN;
    if ~isempty(Y)
        newRow(Y(:,1)) = Y(:,2);
    end
    
    theseViews = state.f(q);
    uniqueTheseViews = unique(theseViews);
    
    sample = zeros(1,length(q));
    
    for i = 1 : length(uniqueTheseViews);
            
        thisView = uniqueTheseViews(i);
        
        % find the conditions that are relevant to this query (in same
        % view)
        theseConditions = find(state.f==thisView & ~isnan(newRow));
        
        % loop over categories
        uc = unique(state.o(thisView,:));
        logProb = zeros(1,length(uc));
        probCRP = ones(1,length(uc));
        
        for ii = 1 : length(uc)
            % assess probability of category assignment based on CRP
            theseRows = state.o(thisView,:)==uc(ii);
            probCRP(ii) = sum(theseRows) ./ (state.O+state.crpPriorC(thisView));
            
            for iii = 1 : length(theseConditions)
                % assess probability of conditions given category
                % this depends on the modeltype
                
                switch state.dataTypes{theseConditions(iii)}

                    case 'asymmetric_beta_bernoulli'
                        sum1 = sum(theseData==1) + ...
                                state.betaBern_s(theseConditions(iii)) .* ...
                                state.betaBern_b(theseConditions(iii));
                        sum0 = sum(theseData==0) + ...
                            state.betaBern_s(theseConditions(iii)) .* ...
                            (1 - state.betaBern_b(theseConditions(iii)));
                        tmpProb = normalize([sum0, sum1]);
                        logProb(ii) = logProb(ii)+ log( tmpProb(newRow(theseConditions(iii))+1) );

                    case 'dirichlet_multinomial'
                        % FIXME

                    case 'normal_inverse_gamma'
                        theseData = state.data(theseRows, theseConditions(iii));
                        theseData = theseData(~isnan(theseData));
                        logProb(ii) = logProb(ii) + ...
                            NG_cat(theseData, newRow(theseConditions(iii)), ...
                            state.NG_mu(theseConditions(iii)), state.NG_k(theseConditions(iii)), ...
                            state.NG_a(theseConditions(iii)), state.NG_b(theseConditions(iii)));
                end
                
            end
            
        end
        
        % consider the probability of a new category
        probCRP(end+1) = state.crpPriorC(thisView) ./ (state.O+state.crpPriorC(thisView));
        logProb(end+1) = 0;
        lengthUC = length(uc)+1;
        uc(end+1) = state.O+2;
        for ii = 1 : length(theseConditions)
            switch state.dataTypes{theseConditions(iii)}

                    case 'asymmetric_beta_bernoulli'
                        thisValue = zeros(1,2);
                        thisValue(newRow(theseConditions(iii))+1) = 1;
                        sum1 = thisValue(2) + sum(theseData==1) + ...
                                state.betaBern_s(theseConditions(iii)) .* ...
                                state.betaBern_b(theseConditions(iii));
                        sum0 = thisValue(1) + sum(theseData==0) + ...
                            state.betaBern_s(theseConditions(iii)) .* ...
                            (1 - state.betaBern_b(theseConditions(iii)));
                        tmpProb = normalize([sum0, sum1]);
                        logProb(lengthUC) = logProb(lengthUC)+ ...
                                log( tmpProb(newRow(theseConditions(iii))+1) );

                    case 'dirichlet_multinomial'
                        % FIXME

                    case 'normal_inverse_gamma'
                        theseData = []; % no data in category
                        logProb(lengthUC) = logProb(lengthUC) + ...
                            NG_cat(theseData, newRow(theseConditions(iii)), ...
                            state.NG_mu(theseConditions(iii)), state.NG_k(theseConditions(iii)), ...
                            state.NG_a(theseConditions(iii)), state.NG_b(theseConditions(iii)));
                end
        end
        % probabilistically choose a category based on the conditions
        logCRP = log(probCRP);
        logP = logCRP + logProb;
        logP = logP - logsumexp(logP);
        p = exp(logP);
        cump = cumsum(p);
        thisCat = uc(find(cump>rand,1));
        
        % generate a prediction based on the category
        % this depends on the modeltype
        theseRows = state.o(thisView,:)==thisCat;
        
        % generate a prediction for each query column in this view
        theseColumns = find(theseViews==thisView);
        for ii = 1 : length(theseColumns)
            sample(theseColumns(ii)) = sampleValue(state.data(theseRows,q(theseColumns(ii))), ...
                                                    q(theseColumns(ii)), state);
        end
        
    end
    
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
    % FIXME
    switch state.dataTypes{q}
        case 'asymmetric_beta_bernoulli'

            sum1 = sum(theseData==1) + state.betaBern_s(q) .* state.betaBern_b(q);
            sum0 = sum(theseData==0) + state.betaBern_s(q) .* (1 - state.betaBern_b(q));
            sample = sample_beta_bernoulli(sum0, sum1);

        case 'dirichlet_multinomal'

            % FIXME

        case 'normal_inverse_gamma'

            % sample from posterior predictive distribution
            len1 = length(theseData);
            meanData = mean(theseData);
            
            b0 = state.NG_b(q);
            a0 = state.NG_a(q);
            k0 = state.NG_k(q);
            mu0 = state.NG_mu(q);
            
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

function sample = sample_beta_bernoulli(sum0, sum1)
    prob = [ sum0./(sum0+sum1), sum1./(sum0+sum1) ];
    cumProb = cumsum(prob);          
    sample = find(rand<cumProb,1)-1;
end