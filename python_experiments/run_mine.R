source('MINE.r')

paste = function(..., sep = '', collapse = NULL)
  .Internal(paste(list(...), sep, collapse))

in.dir = '../../data/'
out.dir = '../../mine/'
par.dir = '../../parameters/'
datasets = readLines(paste(par.dir, 'datasets'))
reps = as.numeric(readLines(paste(par.dir,'reps')))

for(dataset in datasets) {
  for(i in 0:(reps - 1)) {

    pars = strsplit(readLines(paste(par.dir, dataset)),',')
    
    if(length(pars) == 2) {
      par.names = c(pars[[1]][1], pars[[2]][1])
      combos = expand.grid(pars[[1]][-1], pars[[2]][-1])
      combos = data.frame(lapply(combos,as.character),
        stringsAsFactors=F)
    } else {
      par.names = pars[[1]][1]
      combos = cbind(pars[[1]][-1])
    }
    
    all.results = c()
    
    for(j in 1:nrow(combos)) {
      
      file.base = paste(dataset, '-i-', i)
      
      parfix = paste(par.names,combos[j,],sep='-',collapse='-')
      in.file = paste(in.dir, file.base, '-', parfix, '-data.csv')
      temp.out = '/tmp/results'
      
      data = t(read.csv(in.file, header = F))
      
      sink('/dev/null')
      rMINE(data, temp.out, "all.pairs")
      sink()
      
      temp.in = paste(temp.out,
        ',allpairs,cv=0.0,B=n^0.6,Results.csv')
      
      results = read.csv(temp.in, stringsAsFactors=F)
      
      if(nrow(results) > 1) {
        results[,1] = sapply(strsplit(results[,1],' '), function(x) x[2])
        results[,2] = sapply(strsplit(results[,2],' '), function(x) x[2])
        new.rows = cbind(combos[j,], results[,1:3])
        all.results = rbind(all.results, new.rows)
        
      } else {
        all.results = rbind(all.results, c(combos[j,],results[,3]))
      }
      
    }
    
    if(nrow(results) > 1) {
      colnames(all.results) = c(par.names, 'var1', 'var2', 'MIC')
    } else {
      colnames(all.results) = c(par.names, 'MIC')
    }
    
    out.file = paste(out.dir, file.base, '-results.csv')
    write.table(all.results, out.file, quote=F, sep=',',
                row.names=F, col.names=T)
    
  }
}

