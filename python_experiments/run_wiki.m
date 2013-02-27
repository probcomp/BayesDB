
pred = '250';
mcmc = '500';
reps = 1;

for j = 0:(reps - 1)
    for i = [0:6,14:20]
        name = ['wiki-i-' num2str(i)];
        seed = num2str(randi(2^32) - 1);
        out_file = ['../../crosscat-out/' name '-' seed '.txt'];
        run_crosscat('../../data/',name,'correlation',...
            pred,mcmc,seed,'../../crosscat-samples/', out_file);
    end
end
