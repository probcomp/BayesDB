library(lattice)

in.dir = '../../crosscat-results/'
out.dir = '../../crosscat-plots/'
baseline.dir = '../../results/'
data.reps = 1

get.results <- function(experiment, dir = in.dir) {
  results = data.frame()
  for(i in 0:(data.reps - 1)) {
    file.base = paste(experiment,'-i-',i,'-results.csv',sep='')
    in.file = paste(dir, file.base, sep='')
    results = rbind(results, cbind(i,read.csv(in.file, header=F, skip=1)))
  }
  return(results)
}

### plot ring data

png(paste(out.dir, 'ring.png', sep=''))

results <- get.results('ring')
compare <- get.results('ring', baseline.dir)

plot.vars = results[,c(2,4)]
plot.vars[,1] = sapply(plot.vars[,1], function(x) compare[compare[,2] == x,3])

plot(plot.vars,
     xlab = 'Actual Mutual Information',
     ylab = 'Estimated Mutual Information',
     main = 'Ring Data, N = 200')
lines(plot.vars[,1], plot.vars[,1], col = 'red')

dev.off()

### plot simple correlation

true.mi <- function(r)
  -0.5*log(1 - r^2)

est.r2 <- function(mi) {
  sqrt(1 - exp(-2*mi*(mi >= 0)))
}

experiment = 'correlation'

all.results <- get.results(experiment)

ylim = range(all.results[,5])

for(n in unique(all.results[,2])) {

  png(paste(out.dir, experiment, '-n-', n, '.png', sep =''))

  results = all.results[all.results[,2] == n,]

  plot.var = results[,c(3,5)]

  #plot.var[,1] <- true.mi(plot.var[,1])
  plot.var[,1] <- jitter(plot.var[,1])
  plot.var[,2] <- est.r2(plot.var[,2])
  ylim = c(0,1)

  plot(plot.var,
       xlab = 'Actual Mutual Information',
       ylab = 'Estimated Mutual Information',
       main = paste('Correlation, N = ', n, sep=''),
       ylim = ylim)
  lines(plot.var[,1], plot.var[,1], col = 'red')

  dev.off()
}

### plot no correlation with outliers

plot.outliers <- function(experiment, name) {
  png(paste(out.dir, experiment, '.png', sep=''))
  
  results <- get.results(experiment)

  plot.var = results[,c(2,4)]
  
  plot(plot.var,
       xlab = 'Number of Outliers',
       ylab = 'Estimated Mutual Information',
       main = paste(name, ', N = 50'))
  
  dev.off()
}

plot.outliers('outliers', 'Outliers')
plot.outliers('outliers-correlated', 'Anticorrelated Outliers')

### plot pairwise correlation

ns = c('5', '25', '50', '100', '200')
corrs = c('0.0', '0.1', '0.2', '0.3', '0.4',
  '0.5', '0.6', '0.7', '0.8', '0.9', '1.0')

results = read.csv('../../results/correlated-pairs-i-0-results.csv')

for(i in 1:length(ns)) {

  png(paste('../../crosscat-plots/correlated-pairs-i-0-n-',ns[i],'-results.png',
            sep=''))

  par(oma = c(0,0,2,0))
  par(mfrow = c(3, 4))
  
  for(j in 1:length(corrs)) {
    indices = which(results[,1] == as.numeric(ns[i]) &
      results[,2] == as.numeric(corrs[j]))
    ncols = 50
    hits = ncols/2
    misses = ncols*(ncols - 1)/2 - hits
    data = results[indices,]
    tpr = data[,'unadj_tp']/hits
    fpr = data[,'unadj_fp']/misses
    plot(fpr, tpr, 
         main = paste('corr = ',corrs[j],sep=''),
         xlim = c(0,1), ylim = c(0,1))
    tpr = data[,'adj_tp']/hits
    fpr = data[,'adj_fp']/misses
    points(fpr, tpr, col = 'red')

    legend('bottomright', c('unadjusted', 'adjusted'),
           col = c('black', 'red'), pch = 1)
  }

  title(main = paste('Pairwise Correlation Data, N =', ns[i]),
        outer = TRUE)

  dev.off()
}

### plot anova data

plot.anova <- function(file.base, name) {

  results = get.results(file.base)

  diffs = results[,3] - results[,4]
  h = hist(diffs)
  xlim = c(min(0,h$breaks), max(0,h$breaks))
  hist(diffs,
       xlab = 'I(X,Z|Y) - I(Y,Z|X)',
       xlim = xlim,
       main = name)
  abline(v = 0, col='red')
}

out.dir = out.dir + 'anova/'

file.base = 'simple-anova'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + Y = Z')
dev.off()

file.base = 'simple-anova-omitted'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + W = Z')
dev.off()

file.base = 'simple-anova-mixture'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + Y = Z, X,Y ~ mixture')
dev.off()

file.base = 'anova-1'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + Y + XY = Z')
dev.off()

file.base = 'anova-2'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + XY = Z')
dev.off()

file.base = 'anova-3'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'XY = Z')
dev.off()

file.base = 'anova-1-omitted'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + W + XW= Z')
dev.off()

file.base = 'anova-2-omitted'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + XW = Z')
dev.off()

file.base = 'anova-3-omitted'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'XW = Z')
dev.off()

file.base = 'anova-1-mixture'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + Y + XY = Z, X,Y ~ mixture')
dev.off()

file.base = 'anova-2-mixture'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + XY = Z, X,Y ~ mixture')
dev.off()

file.base = 'anova-3-mixture'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'XY = Z, X,Y ~ mixture')
dev.off()

file.base = 'anova-correlated-1'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + Y + XY = Z, X,Y ~ correlated')
dev.off()

file.base = 'anova-correlated-2'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + XY = Z, X,Y ~ correlated')
dev.off()

file.base = 'anova-correlated-3'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'XY = Z, X,Y ~ correlated')
dev.off()

file.base = 'anova-correlated-1-omitted'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + W + XW = Z, X,Y ~ correlated')
dev.off()

file.base = 'anova-correlated-2-omitted'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'X + XW = Z, X,Y ~ correlated')
dev.off()

file.base = 'anova-correlated-3-omitted'
png(paste(out.dir, file.base, '-results.png', sep = ''))
plot.anova(file.base, 'XW = Z, X,Y ~ correlated')
dev.off()
