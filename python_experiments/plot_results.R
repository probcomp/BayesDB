library(lattice)

### plot ring data

pdf('../../plots/ring-i-0-results.pdf')

widths = c('0.1', '0.3', '0.5', '0.7', '0.9')
results = read.csv('../../results/ring-i-0-results.csv')

par(oma = c(0,0,2,0))
par(mfrow = c(2, 3))

for(i in 1:length(widths)) {
  w = widths[i]
  pe = round(results[i,2], 3)
  data = read.csv(paste('../../data/ring-i-0-width-',w,'-data.csv',sep=''),
    header = F)
  plot(data, pch = '.',
       main = paste('H(Y|X)/H(Y) =', pe))
}

plot(results[,'percent_entropy'], results[,'R_squared'], type = 'l',
     ylim = c(0,0.01))

title(main = "Ring Data, N = 1000", outer = TRUE)

dev.off()

### plot simple correlation

ns = c('5', '10', '25', '50', '100')
corrs = c('0.0', '0.1', '0.2', '0.3', '0.4',
  '0.5', '0.6', '0.7', '0.8', '0.9', '1.0')

results = read.csv('../../results/correlation-i-0-results.csv')

k = 0
for(i in 1:length(ns)) {

  png(paste('../../plots/correlation-i-0-results-n-',ns[i],'.png',sep=''))

  par(oma = c(0,0,2,0))
  par(mfrow = c(3, 4))
  
  for(j in 1:length(corrs)) {
    k = k + 1
    data = read.csv(paste('../../data/correlation-i-0-n-',ns[i],
      '-corr-',corrs[j],'-data.csv',sep=''),
      header = F)
    plot(data, pch = '.',
         main = paste('correlation =',corrs[j], sep = ''))
    lines(data[,1], data[,1]*results[k,'beta1'] + results[k,'beta0'],
          col = 'red')
  }

  title(main = paste('Simple Correlation Data N =', ns[i]), outer = TRUE)
  
  dev.off()

}

### plot no correlation with outliers

ns = c('1', '5', '10', '25', '50')

results = read.csv('../../results/outlier-results.csv')

png(paste('../../plots/outlier-results.png',sep=''))

par(oma = c(0,0,2,0))
par(mfrow = c(2,3))

for(i in 1:length(ns)) {
  
  data = read.csv(paste('../../data/outliers-n-',ns[i],
    '-data.csv',sep=''),
    header = F)
  plot(data, pch = '.',
       main = paste('N =',ns[i], sep = ''))
  lines(data[,1], data[,1]*results[i,'beta1'] + results[i,'beta0'],
        col = 'red')
  }

title(main = 'No Correlation + Outliers', outer = TRUE)
  
dev.off()


### plot correlation with outliers

ns = c('1', '5', '10', '25', '50')

results = read.csv('../../results/outlier-correlated-i-0-results.csv')

png(paste('../../plots/outlier-correlated-i-0-results.png',sep=''))

par(oma = c(0,0,2,0))
par(mfrow = c(2,3))

for(i in 1:length(ns)) {
  
  data = read.csv(paste('../../data/outlier-correlated-i-0-n-',ns[i],
    '-data.csv',sep=''),
    header = F)
  plot(data, pch = '.',
       main = paste('N =',ns[i], sep = ''))
  lines(data[,1], data[,1]*results[i,'beta1'] + results[i,'beta0'],
        col = 'red')
  }

title(main = 'Correlation + Outliers', outer = TRUE)

dev.off()


### plot pairwise correlation

ns = c('5', '25', '50', '100', '200')
corrs = c('0.0', '0.1', '0.2', '0.3', '0.4',
  '0.5', '0.6', '0.7', '0.8', '0.9', '1.0')

results = read.csv('../../results/correlated-pairs-i-0-results.csv')

for(i in 1:length(ns)) {

  png(paste('../../plots/correlated-pairs-i-0-n-',ns[i],'-results.png',
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

### plot group correlation

ns = c('5', '25', '50', '100', '200')
corrs = c('0.0', '0.1', '0.2', '0.3', '0.4',
  '0.5', '0.6', '0.7', '0.8', '0.9', '1.0')

results = read.csv('../../results/correlated-halves-i-0-results.csv')

for(i in 1:length(ns)) {

  png(paste('../../plots/correlated-halves-i-0-n-',ns[i],'-results.png',
            sep=''))

  par(oma = c(0,0,2,0))
  par(mfrow = c(3, 4))
  
  for(j in 1:length(corrs)) {
    indices = which(results[,1] == as.numeric(ns[i]) &
      results[,2] == as.numeric(corrs[j]))
    ncols = 50
    hits = 2*ncols/2*(ncols/2 - 1)/2
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

  title(main = paste('Group Correlation Data, N =', ns[i]),
        outer = TRUE)

  dev.off()
}

### plot anova data

plot.anova <- function(file.base) {

  results = read.csv(paste('../../results/', file.base,
    '-i-0-results.csv',
    sep = ''))
  
  data = read.csv(paste('../../data/',file.base,
    '-i-0-data.csv',sep=''),
    header = F)
  colnames(data) = c('x', 'y', 'z')
  
  xlim = range(data[,1])
  ylim = range(data[,2])

  n = 10
  x = seq(xlim[1], xlim[2], length = n)
  y = seq(ylim[1], ylim[2], length = n)
  reg = data.frame(expand.grid(x,y))
  colnames(reg) = c('x', 'y')
  b0 = results[1, 'beta0']
  b1 = results[1, 'beta1']
  b2 = results[1, 'beta2']
  b12 = results[1, 'beta12']
  f <- function(x, y) b0 + b1*x + b2*y + b12*x*y
  reg$z = f(reg$x, reg$y)

  mypanel <- function(x1,y1,z1,x2,y2,z2,...) {
      panel.wireframe(x2,y2,z2,...)
      panel.cloud(x1,y1,z1,...)
    }
  wireframe(data$z ~ data$x * data$y, xlab="X", ylab="Y", zlab="Z",
            panel=mypanel, x2 = reg$x, y2 = reg$y,
            z2 = reg$z, screen = list(x = -90, y = -30, z = 0),
            main = file.base)
}

file.base = 'simple-anova'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'simple-anova-omitted'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-1'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-2'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-3'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()


file.base = 'anova-1-omitted'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-2-omitted'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-3-omitted'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-correlated-1'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-correlated-2'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-correlated-3'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-correlated-1-omitted'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-correlated-2-omitted'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()

file.base = 'anova-correlated-3-omitted'
png(paste('../../plots/', file.base, '-results.png', sep = ''))
plot.anova(file.base)
dev.off()
