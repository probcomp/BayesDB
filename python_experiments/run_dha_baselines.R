source('MINE.r')

in.file = '../../data/dha-data.csv'
out.dir = '../../mine/'
temp.out = '/tmp/results'
      
data = t(read.csv(in.file, header = F))

#### mine ####

sink('/dev/null')
rMINE(data, temp.out, "all.pairs")
sink()
      
temp.in = paste(temp.out,
  ',allpairs,cv=0.0,B=n^0.6,Results.csv',sep='')
      
results = read.csv(temp.in, stringsAsFactors=F)      

results[,1] = sapply(strsplit(results[,1],' '), function(x) x[2])
results[,2] = sapply(strsplit(results[,2],' '), function(x) x[2])
results = results[,1:3]
        
colnames(all.results) = c('var1', 'var2', 'MIC')

out.file = paste(out.dir, 'dha-results.csv', sep='')
write.table(results, out.file, quote=F, sep=',',
            row.names=F, col.names=T)

#### linear regression ####

data = t(data)

f = ncol(data)
results = matrix(NA, f*(f-1)/2, 4)

k = 1
for(i in 1:(f-1)) {
  for(j in (i+1):f) {
    fit = summary(lm(data[,i] ~ data[,j]))
    p = pf(fit$fstatistic[1],fit$fstatistic[2],fit$fstatistic[3],lower.tail=FALSE)
    results[k,] = c(i,j,fit$r.squared,p)
    k = k + 1
  }
}

colnames(results) = c('i', 'j', 'r2', 'p')

write.table(results, file = '../../results/dha-lm.csv',
            sep = ',', row.names = F)
