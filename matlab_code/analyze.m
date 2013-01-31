function state = analyze(state, kernelList, nSteps, c, r, maxIterations, maxTime)
% NOTE: this version does not support maxIterations or maxTime
%     : assume that data are already my kind of state   
%     : To get this to do different types of data, the whole thing needs to
%     be reconstructed
    
    % convert 'all' option to numbers
    if isstr(c) && strcmp(c, 'all');
        clear c;
        c = 1 : state.F;
    end
    
    if isstr(r) && strcmp(r, 'all');
        clear r;
        r = 1 : state.O;
    end 

    % runModel
    for n = 1 : nSteps
        tic
        state = drawSample(state, kernelList, c, r); 
        toc
    end
    
    % saveResults
    name = ['Samples/crossCat_', num2str(round(now*100000))];
    save([name], 'state', 'kernelList', 'nSteps', 'c', 'r');

end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function state = drawSample(state, kernelList, c, r) 
    
    for i = 1 : length(kernelList)
        switch kernelList{i}
            
            case 'columnPartitionHyperparameter'
                state = sampleColumnPartitionHyperparameter(state);
                
            case 'columnPartitionAssignments'
                if state.F > 1
                    state = sampleKinds(state, c);
                end
                
            case 'componentHyperparameters'
                for ii = 1 : length(c)
                    switch state.dataTypes{ii}
                        case 'normal_inverse_gamma'
                            state = sampleComponentHyperparameters_normal_inverse_gamma(state, c(ii));
                        case 'dirichlet_multinomial '
                            % FIXME!
                            disp('FIXME');
                        case 'asymmetric_beta_bernoulli '
                            state = sampleComponentHyperparameters_asymmetric_beta_bernoulli (state, c(ii));
                        otherwise
                            disp([state.dataTypes{ii}, ' is not a valid data type']);
                    end
                end
                
            case 'rowPartitionHyperparameters'
                state = sampleRowPartitionHyperparameter(state);
                
            case 'rowPartitionAssignments'
                state = sampleCategories(state, r);
            
            otherwise
                disp([kernelList{i}, ' is not a valid option']);
        end
    end

end

%~~~~~~~~~~~~~~~~~~~~~~~~~~
% SAMPLE HYPER PARAMETERS
%~~~~~~~~~~~~~~~~~~~~~~~~~~
function state = sampleColumnPartitionHyperparameter(state)  
    % crpPrior kinds
    logP = zeros(1,length(state.crpKRange));
    for i = 1 : length(state.crpKRange)
        state.crpPriorK = state.crpKRange(i);
        logP(i) = crp(state.f, state.crpPriorK); % only need to look at kinds
    end
    % choose state
    this = chooseState(logP);
    state.crpPriorK = state.crpKRange(this);
end
    
function state = sampleRowPartitionHyperparameter(state)  

    % get views
    u = unique(state.f);
    
    for ii = 1 : length(u)
        % crpPrior categories
        logP = zeros(1,length(state.crpCRange));
        for i = 1 : length(state.crpCRange)
            state.crpPriorC(u(ii)) = state.crpCRange(i);
            logP(i) = crp(state.o(u(ii),:), state.crpPriorC(u(ii))); % only need to look at categories
        end
        % choose state
        this = chooseState(logP);
        state.crpPriorC(u(ii)) = state.crpCRange(this);
    end
end

function this = chooseState(logP)
    prob = exp(logP - logsumexp(logP,2));
    cumprob = cumsum(prob);
    this = find(cumprob>rand,1);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%
% normal_inverse_gamma hyperparameters %
%%%%%%%%%%%%%%%%%%%%%%%%%%%
function state = sampleComponentHyperparameters_normal_inverse_gamma(state, f)

    thisK = state.f(f);
    c = unique(state.o(thisK,:));
    
    state = sampleMu(state, f);
    state = sampleA(state, f);
    state = sampleB(state, f);
    state = sampleK(state, f);
    
    % k
    function state = sampleK(state, f)
        logP = zeros(1,length(state.kRange));
        for i = 1 : length(state.kRange)
            for j = 1 : length(c)
                theseData = state.o(thisK,:)==c(j);
                logP(i) = logP(i) + NG(state.data(theseData,f), ...
                                       state.NG_mu(f), state.kRange(i), ... 
                                       state.NG_a(f), state.NG_b(f));
                logP(i) = logP(i) + log(state.paramPrior(i));
            end
        end
        % choose state
        this = chooseState(logP);
        state.NG_k(f) = state.kRange(this)+1;
    end

    % a
    function state = sampleA(state, f)
        logP = zeros(1,length(state.aRange));
        for i = 1 : length(state.aRange)
            for j = 1 : length(c)
                theseData = state.o(thisK,:)==c(j);
                logP(i) = logP(i) + NG(state.data(theseData,f), ...
                                       state.NG_mu(f), state.NG_k(f), ... 
                                       state.aRange(i), state.NG_b(f));
                logP(i) = logP(i) + log(state.paramPrior(i));                               
            end
        end
        % choose state
        this = chooseState(logP);
        state.NG_a(f) = state.aRange(this);
    end

    % b
    function state = sampleB(state, f)
        logP = zeros(1,length(state.bRange(f,:)));
        for i = 1 : length(state.bRange(f,:))
            for j = 1 : length(c)
                theseData = state.o(thisK,:)==c(j);
                logP(i) = logP(i) + NG(state.data(theseData,f), ...
                                       state.NG_mu(f), state.NG_k(f), ...
                                       state.NG_a(f), state.bRange(f,i));
                logP(i) = logP(i) + log(state.paramPrior(i));
            end
        end
        % choose state
        this = chooseState(logP);
        state.NG_b(f) = state.bRange(f,this);
    end

    % mu
    function state = sampleMu(state, f)
        logP = zeros(1,length(state.muRange(f,:)));
        for i = 1 : length(state.muRange(f,:))
            for j = 1 : length(c)
                theseData = state.o(thisK,:)==c(j);
                logP(i) = logP(i) + NG(state.data(theseData,f), ...
                                       state.muRange(f,i), state.NG_k(f), ...
                                       state.NG_a(f), state.NG_b(f));
            end
        end
        % choose state
        this = chooseState(logP);
        state.NG_mu(f) = state.muRange(f,this);
    end
    
end

%%%%%%%%%%%%%%%%%%%%%%%%%%
% asymmetric_beta_bernoulli  Hyperparameters %
%%%%%%%%%%%%%%%%%%%%%%%%%%
function state = sampleComponentHyperparameters_asymmetric_beta_bernoulli (state, f)  
    
    thisK = state.f(f);
    c = unique(state.o(thisK,:));
    
    state = sampleS(state, f);
    state = sampleB(state, f);
    
    % s
    function state = sampleS(state, f)
        logP = zeros(1,length(state.sRange));
        for i = 1 : length(state.sRange)
            for j = 1 : length(c)
                theseData = state.o(thisK,:)==c(j);
                logP(i) = logP(i) + betaBern(state.data(theseData,f), ...
                                       state.sRange(i), state.betaBern_b(f));
                logP(i) = logP(i) + log(state.paramPrior(i));                               
            end
        end
        % choose state
        this = chooseState(logP);
        state.betaBern_s(f) = state.sRange(this);
    end
    
    % b
    function state = sampleB(state, f)
        logP = zeros(1,length(state.bRange));
        for i = 1 : length(state.bRange)
            for j = 1 : length(c)
                theseData = state.o(thisK,:)==c(j);
                logP(i) = logP(i) + betaBern(state.data(theseData,f), ...
                                       state.betaBern_s(f), state.bRange(i));
                logP(i) = logP(i) + log(state.paramPrior(i));                               
            end
        end
        % choose state
        this = chooseState(logP);
        state.betaBern_b(f) = state.bRange(this);
    end

end

%~~~~~~~~~~~~~~~~~~~~~~~~~~
% SAMPLE KINDS
%~~~~~~~~~~~~~~~~~~~~~~~~~~
function state = sampleKinds(state, F)  
    % this includes gibbs moves on features, and M-H move to propose new
    % kinds
    
    for f = F
        k = unique(state.f);
        
        % first gibbs (only makes sense if there is more than one feature in this kind, and there is more than one kind)
        if sum(state.f(f)==state.f)>1 && length(k)>1 
            logP = [];
            for K = k
                state.f(f)=K;

                % crp
                sumF = sum(state.f==K);
                if sumF>1
                    logP(end+1) = log( (sumF-1) ./ (state.F-1+state.crpPriorK) );
                else
                    logP(end+1) = log( state.crpPriorK ./ (state.F-1+state.crpPriorK) );
                end

                logP(end) = logP(end) + scoreFeature(state,f); 
            end
            % choose state
            this = chooseState(logP);
            state.f(f) = k(this);
        end
        
        % then MH, choose new v old
        cut = .5; % percent new
        oldState = state;
        newOld = rand>cut;
        
        if length(k)==1 && newOld==1
            continue;
        end
        
        if newOld == 0 % new
%            disp('new');
            logP = [];
            % sample partition
            newK = setdiff(1:state.F+1,k);
            newK = newK(1);
            state.f(f) = newK;
            % sample new parameter (uniform prob)
            state.crpPriorC(newK) = state.crpCRange(find(state.cumParamPrior>rand,1));
            % sample new partition
            state.o(newK,:) = sample_partition(state.O, state.crpPriorC(newK));
            
            % score new and score old
            logP(1) = scoreFeature(state, f) + ... % score feature
                      log( state.crpPriorK ./ (state.F-1+state.crpPriorK) ) + ... % new kind
                      crp(state.o(newK,:), state.crpPriorC(newK)); % new categories
            logP(2) = scoreFeature(oldState, f) + ... % score feature
                          log( (sum(oldState.f==oldState.f(f))-1) ./ ...
                               (oldState.F-1+oldState.crpPriorK) );
            
            % M-H (t+1 -> t / t -> t+1)
            if sum(oldState.f==oldState.f(f))==1 % deal with single-feature kinds
                % t+1 -> t: prob of new, prob of choosing cat t
                jump(1) = log(cut)+crp(oldState.o(oldState.f(f),:),state.crpPriorC(oldState.f(f)));
                % t -> t+1: prob of new, prob of choosing cat t+1
                jump(2) = log(cut)-crp(state.o(state.f(f),:),state.crpPriorC(newK));
            else
                % t+1 -> t: prob of old, prob of choosing kind @ t+1
                jump(1) = log((1-cut)*(1/length(unique(state.f))));
                % t -> t+1: prob of new, prob of choosing cat t+1
                jump(2) = log(cut)+crp(state.o(newK,:),state.crpPriorC(newK));
            end
            a = logP(1)-logP(2) + jump(1)-jump(2);
            
        else % old
            newK = randi(length(k));
            if newK == state.f(f)
                continue;
            end
            logP = [];
            logP(2) = scoreFeature(oldState,f) + ...
                      log( (sum(oldState.f==oldState.f(f))-1) ./ ...
                          (oldState.F-1+oldState.crpPriorK) );
            state.f(f) = newK;
            logP(1) = scoreFeature(state,f) + ...
                      log( sum(state.f==state.f(f))./(state.F-1+state.crpPriorK) );
            
            % M-H tranisition (t+1 -> t / t -> t+1)
            if sum(oldState.f==oldState.f(f))==1 % single feature kind
                % t+1 -> t: prob of new, prob of choosing cat t
                jump(1) = log(cut)+crp(oldState.o(oldState.f(f),:),state.crpPriorC(oldState.f(f)));
                % t -> t+1: prob of old, prob of choosing kind @ t
                jump(2) = log((1-cut)*(1/length(unique(oldState.f))));
                a = logP(1)-logP(2)+jump(1)-jump(2);
            else
                % t+1 -> t: prob of old, prob of choosing kind (same # kinds)
                jump(1) = 0;
                % t -> t+1: prob of old, prob of choosing kind (same # kinds)
                jump(2) = 0;
                a = logP(1)-logP(2) + jump(1)-jump(2);
            end
        end
        
        a = exp(a);
        
        if a > rand
            % state is adopted
        else
            % return to old state
            state = oldState;
        end
                
    end
end

function logP = crp(cats, gama)
% the probability of a partition under the CRP
    u = unique(cats);
    num = zeros(1,length(u));
    for i = u
        num(i) = sum(cats==i);
    end
    logP = prob_of_partition_via_counts(num, gama);
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
            otherwise
                disp([state.dataTypes{f}, ' is not a valid data type']);
        end
    end
end

%~~~~~~~~~~~~~~~~~~~~~~~~~~
% SAMPLE CATEGORIES
%~~~~~~~~~~~~~~~~~~~~~~~~~~
function state = sampleCategories(state, r)
    k = unique(state.f);
    for K = k
        for O = r
            state = sampleCategoriesK(state,K,O);
        end
    end
end

function state = sampleCategoriesK(state,K,O)
% this p
        
    C = unique(state.o(K,:));
    % create a new category
    empty = setdiff(1:state.O, C);
    if isempty(empty) && max(C)==state.O
        % do nothing
%     elseif isempty(empty)
%         C = [C, length(C)+1];
    else
        C = [C, empty(1)];
    end

    % score alternative categories
    logP = [];
    for c = C
        state.o(K,O) = c;
        logP(end+1) = scoreObject(state,K,O);
    end

    % choose state
    this = chooseState(logP);
    state.o(K,O) = C(this);

end

function logP = scoreObject(state,K,O)
    theseF = find(state.f==K);
    
    % crp
    sumO = sum(state.o(K,:)==state.o(K,O));
    if sumO>1
        logP = log( (sumO-1) ./ (state.O-1+state.crpPriorC(K)) );
    else
        logP = log( state.crpPriorC(K) ./ (state.O-1+state.crpPriorC(K)) );
    end
    %disp(logP);
    
    % score data
    theseData = state.o(K,:)==state.o(K,O);
    theseData(O) = 0; % eliminate this object
    for f = theseF
        switch state.dataTypes{f}
            case 'normal_inverse_gamma'
                logP = logP + NG_cat(state.data(theseData,f), ...
                             state.data(O,f), ...
                             state.NG_mu(f), state.NG_k(f), ...
                             state.NG_a(f), state.NG_b(f) ...
                            );
            case 'dirichlet_multinomial'
                % FIXME
                disp('FIXME');
            case 'asymmetric_beta_bernoulli'
                logP = logP + betaBern_cat(state.data(theseData,f), ...
                                state.data(O,f), ...
                                state.betaBern_s(f), ...
                                state.betaBern_b(f));
            otherwise
                disp([state.dataTypes{f}, ' is not a valid data type']);
        end
    end
    
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% normal_inverse_gamma likelihoods: Normal-Gamma %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

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

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% asymmetric_beta_bernoulli  Likelihood: Beta-bernoulli %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function logProb = betaBern(data, strength, balance)
    
    numTrue = sum(data);
    numFalse = length(data)-numTrue;
    
    fakeTrue = strength*balance;
    fakeFalse = strength*(1-balance);
    
    logProb = betaln(numTrue+fakeTrue, numFalse+fakeFalse) - ...
              betaln(fakeTrue, fakeFalse);
    
end

function logProb = betaBern_cat(data, newData, strength, balance)
    % this is posterior predictive given existing category
    
    numTrue = sum(newData);
    numFalse = length(newData)-numTrue;
    
    fakeTrue = strength*balance + sum(data);
    fakeFalse = strength*(1-balance) + sum(data==0);
    
    logProb = betaln(numTrue+fakeTrue, numFalse+fakeFalse) - ...
              betaln(fakeTrue, fakeFalse);
    
end

function logP = scoreState(state)
    logP = 0;
    logP = logP + crp(state.f, state.crpPriorK);
    
    F = unique(state.f);
    for f = F
        logP = logP + crp(state.o(f,:),state.crpPriorC);
    end
    
    for f = 1 : state.F
        logP = logP + scoreFeature(state, f);
    end
    
end

function s = logsumexp(a, dim)
% Returns log(sum(exp(a),dim)) while avoiding normal_inverse_gammaal underflow.
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

function l = prob_of_partition_via_counts(ns, gama) 

% TESTED
% function l = crp(ns, gama) 
% probability of the partition in ns under a CRP with concentration parameter
% gama (note that gama here is NOT the gamma function but just a number)
%

% Provided by Charles Kemp

ns=ns(ns~=0); % only consider classes that are not empty
k = length(ns); % number of classes
n = sum(ns); %number of samples
l = sum(gammaln(ns))+k*log(gama)+gammaln(gama)-gammaln(n+gama); 
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

function [M, z] = normalize(A, dim)
    % NORMALISE Make the entries of a (multidimensional) array sum to 1
    % [M, c] = normalise(A)
    % c is the normalizing constant
    %
    % [M, c] = normalise(A, dim)
    % If dim is specified, we normalise the specified dimension only,
    % otherwise we normalise the whole array.

    if nargin < 2
      z = sum(A(:));
      % Set any zeros to one before dividing
      % This is valid, since c=0 => all i. A(i)=0 => the answer should be 0/1=0
      s = z + (z==0);
      M = A / s;
    elseif dim==1 % normalize each column
      z = sum(A);
      s = z + (z==0);
    %   M = A ./ (d'*ones(1,size(A,1)))';
    %   M = A ./ repmatC(s, size(A,1), 1);
      M = A ./ repmat(s, size(A,1), 1);
    %   M = bsxfun(@rdivide,A,s);
    else
      % Keith Battocchi - v. slow because of repmat
      z=sum(A,dim);
      s = z + (z==0);
      L=size(A,dim);
      d=length(size(A));
      v=ones(d,1);
      v(dim)=L;
    %   c=repmat(s,v);
      c=repmat(s,v');
      M=A./c;
    %   M = bsxfun(@rdivide,A,s);
    end
end