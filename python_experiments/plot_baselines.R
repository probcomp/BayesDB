library(lattice)

paste = function(..., sep = '', collapse = NULL)
  .Internal(paste(list(...), sep, collapse))

out.dir = '../../plots/'
baseline.dir = '../../results/'
mine.dir = '../../mine/'
data.reps = 5

get.results <- function(experiment, dir, reps = data.reps) {
  results = data.frame()
  for(i in 0:(reps - 1)) {
    file.base = paste(experiment,'-i-',i,'-results.csv')
    in.file = paste(dir, file.base)
    raw = read.csv(in.file, header=T)
    results = rbind(results, cbind(i,raw))
  }
  return(results)
}

### plot ring data

png(paste(out.dir, 'ring-mine.png'))

results <- get.results('ring', mine.dir)
compare <- get.results('ring', baseline.dir)
compare = aggregate(compare[,3], list(compare[,2]), mean)

plot.vars = results[,c(2,3)]
plot.vars[,1] = apply(cbind(plot.vars[,1]), 1,
           function(x) compare[[2]][compare[[1]] == x[1]])
colnames(plot.vars) <- c('x','y')

plot.vars[,1] = round(plot.vars[,1], 3)

b = boxplot(y ~ x, data = plot.vars,
  xlab = 'Empirical Mutual Information',
  ylab = 'MIC',
  ylim = c(0,1))

dev.off()

png(paste(out.dir, 'ring-corr.png'))

results <- get.results('ring', baseline.dir)
compare <- get.results('ring', baseline.dir)
compare = aggregate(compare[,3], list(compare[,2]), mean)

plot.vars = results[,c(2,4)]
plot.vars[,1] = apply(cbind(plot.vars[,1]), 1,
           function(x) compare[[2]][compare[[1]] == x[1]])
colnames(plot.vars) <- c('x','y')

plot.vars[,1] = round(plot.vars[,1], 3)

b = boxplot(y ~ x, data = plot.vars,
  xlab = 'Empirical Mutual Information',
  ylab = expression(R^2),
  ylim = c(0,1))

dev.off()

### plot simple correlation

true.mi <- function(r)
  -0.5*log(1 - r^2)

est.r2 <- function(mi) {
  sqrt(1 - exp(-2*mi*(mi >= 0)))
}

plot.correlation <- function(baseline) {
  
  experiment = 'correlation'
  if(baseline == 'mine') {
    all.results <- get.results(experiment, mine.dir)
    ylab = 'MIC'
    inds = c(3,4)
  } else {
    all.results <- get.results(experiment, baseline.dir)
    ylab = expression(R^2)
    inds = c(3,6)
  }
  
  for(n in unique(all.results[,2])) {

    png(paste(out.dir, experiment, '-n-', n, '-',baseline,
              '.png'))
    
    results = all.results[all.results[,2] == n,]
    
    plot.vars = results[,inds]
    
    ylim = c(0,1)
    
    colnames(plot.vars) <- c('x','y')
    
    b = boxplot(y ~ x, data = plot.vars,
      xlab = 'Ground Truth Correlation',
      ylab = ylab,
      ylim = c(0,1))
    
    dev.off()
  }
}

plot.correlation('mine')
plot.correlation('baseline')

### plot outliers

plot.outliers <- function(experiment, name) {

  png(paste(out.dir, experiment, '-mine.png'))
  
  results <- get.results(experiment, mine.dir)

  plot.vars = results[,c(2,3)]
  
  colnames(plot.vars) <- c('x','y')

  b = boxplot(y ~ x, data = plot.vars,
    xlab = 'Number of Outliers',
    ylab = 'MIC',
    ylim = c(0,1))
  
  dev.off()

  png(paste(out.dir, experiment, '-corr.png'))
  
  results <- get.results(experiment, baseline.dir)

  plot.vars = results[,c(2,5)]
  
  colnames(plot.vars) <- c('x','y')

  b = boxplot(y ~ x, data = plot.vars,
    xlab = 'Number of Outliers',
    ylab = expression(R^2),
    ylim=c(0,1))

  
  dev.off()
}

plot.outliers('outliers', 'Outliers')
plot.outliers('outliers-correlated', 'Anticorrelated Outliers')
