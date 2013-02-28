import crosscat_helper as cc

hist_reps = 3#5
n_pred_samples = '250'#'250'
n_mcmc_iter = '500'#'500'
datasets = range(0,7) + range(14,21)

file_base = 'wiki'

f = open(out_folder + file_base + '-results.csv', 'w')
if parse:
    job_ids = get_job_ids(file_base)
    f.write('index,rep,mutual_info\n')
    
k = 0
for j in range(hist_reps):
    for i in datasets:
        
        if parse:
            job_id = int(job_ids[k])
            k += 1
            h = parse_out('correlation', job_id)[0].split(',')[2]
            f.write(str(i) + ',' + str(j) + ',' + h + '\n')
        else:
            name = file_base + '-i-' + str(i)
            job_id = run(name, 'correlation')
            f.write(str(i) + ',' + str(j) + ',' + str(job_id) + '\n')

f.close()
