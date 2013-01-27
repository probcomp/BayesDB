function state_to_json(state, rowLabelFile, colLabelFile, colValueConverter)

    id = num2str(round(now*100000));
    
    % put state into cannonical order (largest views/categories have #1 etc)
    % first views:
    uv = unique(state.f);
    counts = [];
    for v = uv
        counts(end+1) = sum(state.f==v);
    end
    [a, b] = sort(counts, 'descend');
    state.f = -state.f;
    o = state.o;
    state.o = [];
    crpPriorC = state.crpPriorC;
    state.crpPriorC = [];
    for i = 1 : length(b)
        state.f(state.f==-uv(i)) = i;
        state.o(i,:) = o(uv(i),:);
        state.crpPriorC(i) = crpPriorC(uv(i));
    end
    % now do the same for categories:
    for v = 1 : max(state.f)
        uc = unique(state.o(v,:));
        counts = [];
        for c = uc
            counts(end+1) = sum(state.o(v,:)==c);
        end
        [a, b] = sort(counts, 'descend');
        state.o(v,:) = -state.o(v,:);
        for i = 1 : length(b)
            state.o(v,state.o(v,:)==-uc(i)) = i;
        end
    end
    
    % create a matrix with the posterior predictive distribution for each
    % cell
    logProbMat = posteriorPredictiveCell(state);
    
    % now sort things. 
    [col_a col_b] = sort(state.f, 'ascend');
    state.f = col_a;
    
    sumCol = sum(logProbMat);
    for i = 1 : max(state.f)
        theseC = find(state.f == i);
        [tmp_a, tmp_b] = sort(sumCol(theseC), 'descend');
        col_b(theseC) = col_b(theseC(tmp_b));
    end
    % now resort everything by col_b
    state.data = state.data(:,col_b);
    state.dataTypes = state.dataTypes(col_b);
    if isfield(state, 'betaBern_s')
        state.betaBern_s = state.betaBern_s(col_b);
    end
    if isfield(state, 'betaBern_b')
        state.betaBern_b = state.betaBern_b(col_b);
    end
    % FIXME: add categoricalClosed
    if isfield(state, 'NG_mu')
        state.NG_mu = state.NG_mu(col_b);
    end
    if isfield(state, 'NG_a')
        state.NG_a = state.NG_a(col_b);
    end
    if isfield(state, 'NG_b')
        state.NG_b = state.NG_b(col_b);
    end
    if isfield(state, 'NG_k')
        state.NG_k = state.NG_k(col_b);
    end
    % need to resort names and value converters too! these are done later
    
    % now deal with rows within views
    rowsWithinViews = zeros(max(state.f), state.O);
    for i = 1 : max(state.f)
        theseColumns = state.f==i;
        for ii = 1 : max(state.o(i,:))
            theseRows = find(state.o(i,:)==ii);
            sumRow = sum(logProbMat(theseRows, theseColumns),2);
            [row_a, row_b] = sort(sumRow, 'descend');
            % FIXME: how to integrate this into the state???!!
            firstZero = find(rowsWithinViews(i,:)==0,1);
            rowsWithinViews(i,firstZero:firstZero+length(theseRows)-1) = theseRows(row_b); 
        end
    end
                
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % BUILD M_c
    % name to index
    % index to name
    % column metadata
    %   modeltype
    %   code to value
    %   value to code
    
    % read in labels
    fid = fopen([colLabelFile, '.csv']);
    tmp = textscan(fid, '%s', 'Delimiter', ',');
    colLabel = tmp{1};
    % resort
    colLabel = colLabel(col_b);
    fclose(fid);
    
    % read in conversion
    fid = fopen([colValueConverter, '.csv']);
    tmp = textscan(fid, '%s', 'Delimiter', ',');
    colValConvert = tmp{1};
    fclose(fid);
    
    % build name to index
    M_c = struct('name_to_idx', []);
    for i = 1 : length(colLabel)
        blank = strfind(colLabel{i}, ' ');
        colLabel{i}(blank) = '_';
        M_c.name_to_idx = setfield(M_c.name_to_idx, colLabel{i}, num2str(i-1));
    end
    
    % list with modeltype, code to value, value to code
    column_metadata = '"column_metadata":[';
    last = 1;
    for i = 1 : length(state.dataTypes)
        string = '{"modeltype":';
        switch state.dataTypes{i}
            case 'binary'
                % add modeltype
                string = strcat(string, '"asymmetric_beta_bernoulli",');
                % add code_to_value
                % Note: need to deal with reordering of columns
                string = strcat(string, '"code_to_value":{"', ...
                                         colValConvert{col_b(last)*2-1}, '":"0","', ...
                                         colValConvert{col_b(last)*2}, '":"1"},');
                % add value_to_code
                string = strcat(string, '"value_to_code":{', ...
                                         '"0":"', colValConvert{col_b(last)*2-1}, '",', ...
                                         '"1":"', colValConvert{col_b(last)*2}, '"}}');                
            case 'categoricalClosed'
                % FIXME
            case 'numeric'
                 % add modeltype
                string = strcat(string, '"normal_inverse_gamma",');
                % add code_to_value
                string = strcat(string, '"code_to_value":{},');
                % add value_to_code
                string = strcat(string, '"value_to_code":{}}');
        end
        column_metadata = strcat(column_metadata, string, ',');
        last = last + 1;
    end
    % remove last comma
    column_metadata = strcat(column_metadata(1:end-1), ']');
    
    S = JSON.dump(M_c);

    % build index to name
    num2col = '"idx_to_name":{';
    for i = 1 : length(colLabel)
        tmp = ['"', num2str(i-1),'":"', colLabel{i},'",'];
        num2col = strcat(num2col, tmp);
    end
    num2col = strcat(num2col(1:end-1), '}');
    S = strcat(S(1:end-1), ',', num2col, S(end));
    
    Mc = strcat(S(1:end-1), ',', column_metadata, S(end));
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % build X_L
    % column_partition
    %   hypers:
    %   assignments:
    %   counts:
    % column_hypers
    %   fixed
    %   FIXME-rest depend on modeltype
    % view_state (one for each view)
    %   row_partition_model 
    %      hypers
    %         log_alpha
    %      counts
    %   column_names
    %   column_component_suffstats
    %      FIXME: depend on modeltype
    %
    
    % column_partition
    X_L.column_partition.hypers.log_alpha = state.crpPriorK;
    X_L.column_partition.assignments = state.f-1;
    X_L.column_partition.counts = []; % this gets done later 

    % column hypers
    for f = 1 : state.F
        X_L.column_hypers{f}.fixed = 'false';
        
        switch state.dataTypes{f}

            case 'numeric'
                X_L.column_hypers{f}.mu = state.NG_mu(f);
                X_L.column_hypers{f}.log_kappa = state.NG_k(f);
                X_L.column_hypers{f}.log_alpha = state.NG_a(f);
                X_L.column_hypers{f}.log_beta = state.NG_b(f);
                
            case 'categoricalClosed'
                % FIXME
                
            case 'binary'
                X_L.column_hypers{f}.log_strength = state.betaBern_s(f);
                X_L.column_hypers{f}.balance = state.betaBern_b(f);
        end
        
    end
    
    % view state
    vu = unique(state.f);
    X_L.view_state = {};
    ctr = 1;
    for v = vu
        X_L.view_state{ctr}.row_partition_model.hypers.log_alpha = ...
            state.crpPriorC(v);
        X_L.column_partition.counts(ctr) = sum(state.f==v);
        
        % deal with each column in view
        these = find(state.f==v);
        for i = 1 : length(these)
            X_L.view_state{ctr}.column_names{i} = colLabel{these(i)};
            cu = unique(state.o(v,:));
            
            for ii = 1 : length(cu)
                theseO = state.o(v,:)==cu(ii);
                % compute category counts
                X_L.view_state{ctr}.row_partition_model.counts(ii) = sum(theseO);
                
                switch state.dataTypes{these(i)}
                    case 'numeric'
                        X_L.view_state{ctr}.column_component_suffstats{i}{ii}.sum_x = ...
                            sum(state.data(theseO,these(i)));
                        X_L.view_state{ctr}.column_component_suffstats{i}{ii}.sum_x_sq = ...
                            sum(state.data(theseO,these(i)).^2);
                        X_L.view_state{ctr}.column_component_suffstats{i}{ii}.N = ...
                            sum(~isnan(state.data(theseO,these(i))));
                        
                    case 'categoricalClosed'
                        % FIXME
                        
                    case 'binary'
                        X_L.view_state{ctr}.column_component_suffstats{i}{ii}.zero_count = ...
                            sum(state.data(theseO,these(i))==0);
                        X_L.view_state{ctr}.column_component_suffstats{i}{ii}.one_count = ...
                            sum(state.data(theseO,these(i)));
                        X_L.view_state{ctr}.column_component_suffstats{i}{ii}.N = ...
                            X_L.view_state{ctr}.column_component_suffstats{i}{ii}.one_count + ...
                            X_L.view_state{ctr}.column_component_suffstats{i}{ii}.zero_count;
                        
                end

            end
        end
        ctr = ctr + 1;
    end
    
    XL = JSON.dump(X_L);
    % find "zero_count" and replace with "0_count"
    % find "one_count" and replace with "1_count"
    XL = strrep(XL, 'zero_count', '0_count');
    XL = strrep(XL, 'one_count', '1_count');
    % deal with the cases where counts does not have brackets around it
    countsWithoutBrackets = regexp(XL, '"counts":\w*,', 'match');
    for i = 1 : length(countsWithoutBrackets)
        tmp = countsWithoutBrackets{i};
        beginning = strfind(tmp, ':');
        tmp1 = [tmp(1:beginning), '[', tmp(beginning+1:end-1), ']', tmp(end)];
        XL = regexprep(XL, tmp, tmp1);
    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % build X_D
    % rowPartitionAssignments 
    
    tmp = [];
    uk = unique(state.f);
    for i = 1 : length(uk)
        tmp(i,:) = state.o(uk(i),:)-1;
    end  
    X_D = tmp;
    
    % FIXME: reorder categories in views
    % FIXME: reorder rows in categories
    
    XD = JSON.dump(X_D);
    
    % deal with case where there are not double brackets
    if ~strcmp(XD(1:2), '[[')
       XD = ['[', XD, ']']; 
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % BUILD M_r
    % name to index
    % index to name
    
    % read in labels
    fid = fopen([rowLabelFile, '.csv']);
    tmp = textscan(fid, '%s', 'Delimiter', ',');
    rowLabels = tmp{1};
    fclose(fid);
    % build struct
    M_r = struct('name_to_idx', []);
    for i = 1 : length(rowLabels)
        M_r.name_to_idx = setfield(M_r.name_to_idx, rowLabels{i}, num2str(i-1));
    end
    
    S = JSON.dump(M_r);
    
    % build index to name
    num2row = '"idx_to_name":{';
    for i = 1 : length(rowLabels)
        tmp = ['"', num2str(i-1),'":"', rowLabels{i},'",'];
        num2row = strcat(num2row, tmp);
    end
    num2row = strcat(num2row(1:end-1), '}');
    Mr = strcat(S(1:end-1), ',', num2row, S(end));
        
    % build data table!
    T.dimensions = size(state.data);
    T.orientation = 'row_major';
    T.data = state.data;
    t = JSON.dump(T);
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % build full state and print! %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    clear S;
    S = strcat('{"M_c":', Mc, ',"M_r":', Mr, ',"X_L":', XL, ',"X_D":', XD, ',"T":', t, '}');

    beginning = strfind(rowLabelFile, '/')+1;
    ending = strfind(rowLabelFile(beginning:end), '_')-2;
    
    filename = rowLabelFile(beginning:beginning+ending);
    fid = fopen([filename,'_', id,'.json'], 'w');
    fprintf(fid, '%s\n', S);
    fclose(fid);
    
end


function logProbMat = posteriorPredictiveCell(state)

    logProbMat = zeros(state.O, state.F);
    
    for i = 1 : state.F
        
        for ii = 1 : state.O
            
            % find the rows in this category
            theseRows = state.o(state.f(i),:)==state.o(state.f(i),ii);
            theseRows(ii) = 0; % zero out this object
            
            % FIXME: switch on types of data
            switch state.dataTypes{i}
                case 'binary'
                    logProbMat(ii,i) = betaBern_cat(state.data(theseRows,i), ...
                                    state.data(ii,i), state.betaBern_s(i), ...
                                    state.betaBern_b(i));
                case 'categoricalClosed'
                    disp('categoricalClosed not implemented yet!');
                    
                case 'numeric'
                    logProbMat(ii,i) = NG_cat(state.data(theseRows,i), ...
                                        state.data(ii,i), state.NG_mu(i), ...
                                        state.NG_k(i), state.NG_a(i), ...
                                        state.NG_b(i));
            end
        end
    end
    
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
