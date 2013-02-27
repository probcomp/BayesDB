
reps = 1;
pred = 200;

for i = [0:6,14:20]
    
    s = nan(pred*reps, state.F);
    
    name = ['wiki-i-' num2str(i)];
    
    
    l = 0;
    for j = 0:(reps - 1)
        
        load(['../../crosscat-samples/' name '-rep-' num2str(j) '.mat'])
        
        for k = 1:pred
            l = l + 1;
            s(l,:) = simple_predictive_sample_newRow(state, [], 1:state.F);
        end
    end
    
    out_file = ['../../crosscat-out/' name '.csv'];
    csvwrite(out_file, s);
    
end
