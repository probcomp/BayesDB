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
results = matrix(NA, f*(f-1)/2, 3)

for(i in 1:(f-1)) {
  for(j in 2:f) {
    fit = lm(data[,i] ~ data[,j])
  }
}
