function prob = simple_predictive_probability_newRows(state, Y, Q)
    % note this version assumes that the only kinds of problems we deal
    % with are new row prediction. we should actually implement the full
    % version (like simple_predictive_sample)
    % Y is a struct with two fields: indices and values. indices is a vector are
    % columns, values are values
    % Q is a struct with two fields: indices and values. indices is a vector with
    % column indices, values are values
    % 
    % example:
    % Y.indices = [];
    % Y.values = [];
    % Q.indices = [1];
    % Q.values = 0;
    % prob = simple_predictive_probability_newRows(state, Y, Q)
    
    newRow = zeros(1,state.F);
    newRow(newRow==0) = NaN;
    newRow(Y.indices) = Y.values;
    
    prob = zeros(length(Q.values),1);
    
    for i = 1 : length(Q.indices)
        
        thisView = state.f(Q.indices);
        theseFeatures = find(state.f==thisView);
        theseFeatures = intersect(theseFeatures, Y.indices);
        
        uc = unique(state.o(thisView,:));
        logP = zeros(1,length(uc));
        
        logQueryProb = zeros(1,length(uc));
        
        for ii = 1 : length(uc)
           
            % score CRP probability
            logP(ii) = log(sum(state.o(thisView,:)==uc(ii)) ./ ...
                        (state.O + state.crpPriorC(thisView)));
            
            % score likelihood
            for iii = 1 : length(theseFeatures)
                theseData = state.data(state.o(thisView,:)==uc(ii),theseFeatures(iii));
                logP(ii) = logP(ii) + posteriorPredictive(state, theseData, ...
                                newRow(theseFeatures(iii)), theseFeatures(iii));
            end
            
            theseData = state.data(state.o(thisView,:)==uc(ii), Q.indices(i));
            logQueryProb(ii) =  posteriorPredictive(state, theseData, ...
                                Q.values(i), Q.indices(i));
            
        end
        
        % consider probability of new category
        logP(end+1) = log(state.crpPriorC(thisView) ./ ...
                        (state.O + state.crpPriorC(thisView)));
        for iii = 1 : length(theseFeatures)
            theseData = []; % no data here
            logP(end) = logP(end) + posteriorPredictive(state, theseData, ...
                            newRow(theseFeatures(iii)), theseFeatures(iii));
        end
        
        logP = logP - logsumexp(logP);
        
        logQueryProb(end+1) = posteriorPredictive(state, [], Q.values(i), Q.indices(i));
        
        % evaluate posterior predictive probability of Q weighted by categories
        prob(i) = sum(exp(logQueryProb+logP));
        
    end
end

function logP = posteriorPredictive(state, theseData, newRowValue, thisFeature)
    

    switch state.dataTypes{thisFeature}
        case 'asymmetric_beta_bernoulli'
            % count ones
            oneCount = sum(theseData==1);
            % count zeros
            zeroCount = sum(theseData==0);
            % compute probability
            prob = (oneCount + state.betaBern_s(thisFeature).*state.betaBern_b(thisFeature)) ./ ...
                   (oneCount + zeroCount + state.betaBern_s(thisFeature));
            if newRowValue==1
                % do nothing
            elseif newRowValue==0
                prob = 1 - prob;
            end
            logP = prob;
            
        case 'multinomial_dirichlet'
            % FIXME
            
        case 'normal_inverse_gamma'
            logP = NG_cat(theseData, newRowValue, state.NG_mu(thisFeature), ...
                        state.NG_k(thisFeature), state.NG_a(thisFeature), ...
                        state.NG_b(thisFeature));
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