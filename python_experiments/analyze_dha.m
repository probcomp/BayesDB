reps = 10;

load(['../../crosscat-samples/dha-0.mat'])

feature_z = zeros(state.F, state.F);

for i = 0:(reps - 1)
    load(['../../crosscat-samples/dha-' num2str(i) '.mat'])
    for j = 1:(state.F - 1)
        for k = (j + 1):state.F
            feature_z(j,k) = feature_z(j,k) + (state.f(j) == state.f(k));
        end
    end
end

feature_z = feature_z./reps;

dlmwrite('../../crosscat-results/dha-z-results.csv',',');