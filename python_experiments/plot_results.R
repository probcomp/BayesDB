
### plot ring data

pdf('../../plots/ring-results.pdf')

widths = c('0.1', '0.3', '0.5', '0.7', '0.9')
results = read.csv('../../results/ring-results.csv')

par(oma = c(0,0,2,0))
par(mfrow = c(2, 3))

for(i in 1:length(widths)) {
  w = widths[i]
  pe = round(results[i,2], 3)
  data = read.csv(paste('../../data/ring-width-',w,'-data.csv',sep=''),
    header = F)
  plot(data, pch = '.',
       main = paste('H(Y|X)/H(Y) =', pe))
}

plot(results[,'percent_entropy'], results[,'R_squared'], type = 'l',
     ylim = c(0,0.01))

title(main = "Ring Data, N = 1000", outer = TRUE)

dev.off()


### plot simple regression

pdf('../../plots/simple-regression-results.pdf')

ns = c('10', '50', '100')
sds = c('0.1', '0.4', '0.8', '2')

results = read.csv('../../results/regression-results.csv')

par(oma = c(0,0,2,0))
par(mfrow = c(3, 4))

k = 0
for(i in 1:length(ns)) {
  for(j in 1:length(sds)) {
    k = k + 1
    data = read.csv(paste('../../data/regression-n-',ns[i],
      '-sd-',sds[j],'-data.csv',sep=''),
      header = F)
    plot(data, pch = '.',
         main = paste('N = ', ns[i],', sd =',sds[j], sep = ''))
    lines(data[,1], data[,1]*results[k,'beta1'] + results[k,'beta0'],
          col = 'red')
  }
}

title(main = 'Simple Regression Data', outer = TRUE)
  
dev.off()


### plot outlier regression

pdf('../../plots/outlier-regression-results.pdf')

ns = c('10', '50', '100')
sds = c('0.1', '0.4', '0.8', '2')

results = read.csv('../../results/outlier-regression-results.csv')

par(oma = c(0,0,2,0))
par(mfrow = c(3, 4))

k = 0
for(i in 1:length(ns)) {
  for(j in 1:length(sds)) {
    k = k + 1
    p = round(results[k,'F_pvalue'], 2)
    data = read.csv(paste('../../data/outlier-regression-n-',ns[i],
      '-sd-',sds[j],'-data.csv',sep=''),
      header = F)
    plot(data, pch = '.',
         main = paste('N = ', ns[i],', sd = ',sds[j],sep=''),
         sub = paste('(p-value = ',p,')',sep = '') )
    lines(data[,1], data[,1]*results[k,'beta1'] + results[k,'beta0'],
          col = 'red')
    lines(data[,1], data[,1])
  }
}

title(main = 'Uniform Outlier Regression Data, epsilon = 0.1', outer = TRUE)
  
dev.off()


### plot pairwise regression

pdf('../../plots/pairwise-regression-results.pdf')

ns = c('2', '10')
sds = c('0.1', '2')

results = read.csv('../../results/pairwise-regression-results.csv')

par(oma = c(0,0,2,0))
par(mfrow = c(2, 2))

for(i in 1:length(ns)) {
  for(j in 1:length(sds)) {
    indices = which(results[,1] == ns[i] & results[,2] == sds[j])
    pairs = as.numeric(ns[i])
    hits = pairs
    misses = pairs*(pairs - 1)/2
    data = results[indices,]
    tpr = data[,'unadj_tp']/hits
    fpr = data[,'unadj_fp']/misses
    plot(fpr, tpr, 
         main = paste('pairs = ', ns[i],', sd = ',sds[j],sep=''),
         xlim = c(0,1), ylim = c(0,1))
    tpr = data[,'adj_tp']/hits
    fpr = data[,'adj_fp']/misses
    points(fpr, tpr, col = 'red')

    legend('bottomright', c('unadjusted', 'adjusted'),
           col = c('black', 'red'), pch = 1)
  }
}

title(main = 'Pairwise Regression Data', outer = TRUE)
  
dev.off()

