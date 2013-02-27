library(lattice)

paste = function(..., sep = '', collapse = NULL)
  .Internal(paste(list(...), sep, collapse))

in.dir = '../../crosscat-results/'
out.dir = '../../crosscat-plots/'
baseline.dir = '../../results/'
mine.dir = '../../mine/'
data.reps = 3
hist.reps = 10

get.results <- function(experiment, dir = in.dir, reps = data.reps) {
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

png(paste(out.dir, 'ring.png'))

results <- get.results('ring')
compare <- get.results('ring', baseline.dir)
compare = aggregate(compare[,3], list(compare[,2]), mean)

plot.vars = results[,c(2,4)]
plot.vars[,1] = apply(cbind(plot.vars[,1]), 1,
           function(x) compare[[2]][compare[[1]] == x[1]])

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

  png(paste(out.dir, experiment, '-n-', n, '.png'))

  results = all.results[all.results[,2] == n,]

  plot.var = results[,c(3,5)]

  #plot.var[,1] <- true.mi(plot.var[,1])
  plot.var[,1] <- jitter(plot.var[,1])
  plot.var[,2] <- est.r2(plot.var[,2])
  ylim = c(0,1)

  plot(plot.var,
       xlab = 'Ground Truth Correlation',
       ylab = 'Estimated Correlation',
       main = paste('Correlation, N = ', n, sep = ' '),
       ylim = ylim)
  lines(plot.var[,1], plot.var[,1], col = 'red')

  dev.off()
}

### plot no correlation with outliers

plot.outliers <- function(experiment, name) {
  png(paste(out.dir, experiment, '.png'))
  
  results <- get.results(experiment)

  plot.var = results[,c(2,4)]
  
  plot(plot.var,
       xlab = 'Number of Outliers',
       ylab = 'Estimated Transformed Mutual Information',
       main = paste(name, ', N = 50', sep = ' '))
  
  dev.off()
}

plot.outliers('outliers', 'Outliers')
plot.outliers('outliers-correlated', 'Anticorrelated Outliers')

### plot pairwise correlation

count.hits = function(vars, values, threshold, experiment) {
  tp = 0
  fp = 0
  for(i in 1:nrow(vars)) {
    pair = sort(vars[i,])
    guess = values[i] >= threshold
    if(experiment == 'correlated-pairs') {
      if((pair[1] %% 2) == 1 & (pair[2] - pair[1]) == 1) {
        tp = tp + guess 
      } else {
        fp = fp + guess
      }
    } else {
      if((pair[1] <= 25) == (pair[2] <= 25)) {
        tp = tp + guess
      } else {
        fp = fp + guess
      }
    }
  }
  return(c(fp,tp))
}

plot.pairwise <- function(experiment) {

cc.results = get.results(experiment, reps = 1)
lm.results = get.results(experiment, baseline.dir, reps = 1)
mine.results = get.results(experiment, mine.dir, reps = 1)

ns = unique(cc.results[,'n'])
corrs = unique(cc.results[,'corr'])

for(i in 1:length(ns)) {
  
  png(paste(out.dir, experiment, '-n-', ns[i], '.png'))
  
  par(oma = c(0,0,2,0))
  par(mfrow = c(3, 4))
  
  for(j in 1:length(corrs)) {

    indices = which(lm.results[,2] == ns[i] &
      lm.results[,3] == corrs[j])

    ncols = 50
    if(experiment == 'correlated-pairs') {
      hits = ncols/2
      misses = ncols*(ncols - 1)/2 - hits
    } else {
      hits = 2*ncols/2*(ncols/2 - 1)/2
      misses = ncols*(ncols - 1)/2 - hits
    }
    
    data = lm.results[indices,]
    tpr = data[,'unadj_tp']/hits
    fpr = data[,'unadj_fp']/misses
    plot(fpr, tpr, 
         main = paste('corr = ',corrs[j]),
         xlim = c(0,1), ylim = c(0,1))
    tpr = data[,'adj_tp']/hits
    fpr = data[,'adj_fp']/misses
    points(fpr, tpr, col = 'red')

    legend('bottomright', c('unadjusted', 'adjusted'),
           col = c('black', 'red'), pch = 1)

    indices = which(cc.results[,'n'] == as.numeric(ns[i]) &
      cc.results[,'corr'] == as.numeric(corrs[j]))
    data = cc.results[indices,]
    data[,'mutual_info'] = est.r2(data[,'mutual_info'])

    ps = seq(-0.1,1.1,length=13)
    #thresholds = seq(-0.1,1.1,length=13)
    thresholds = 0

    by = list(data[,1], data[,5], data[,6])
    counts = sapply(thresholds, function(t) data[,7] > t)/hist.reps
    values = apply(counts, 2, aggregate, by, sum)
    vars = values[[1]][,c(2,3)]
    values = lapply(values, function(x) x[4])
    values = data.frame(values)
    
    if(experiment == 'correlated-pairs') {
      truth = (vars[,2] %% 2) == 1 & (vars[,1] - vars[,2]) == 1
    } else {
      truth = (vars[,1] <= 25) == (vars[,2] <= 25)
    }

    guesses = lapply(ps, function(p) (values > p) & truth)
    tp = lapply(guesses, function(x) apply(x, 2, sum))

    guesses = lapply(ps, function(p) (values > p) & !truth)
    fp = lapply(guesses, function(x) apply(x, 2, sum))

    tpr = unlist(tp)/hits
    fpr = unlist(fp)/misses
    
    points(fpr, tpr, col = 'blue')
    
    indices = which(mine.results[,'n'] == as.numeric(ns[i]) &
      mine.results[,'corr'] == as.numeric(corrs[j]))
    data = mine.results[indices,]

    values = data[,6]
    vars = data[,c(4,5)]
    
    if(experiment == 'correlated-pairs') {
      truth = (vars[,2] %% 2) == 1 & (vars[,1] - vars[,2]) == 1
    } else {
      truth = (vars[,1] <= 25) == (vars[,2] <= 25)
    }

    guesses = lapply(ps, function(p) (values > p) & truth)
    tp = lapply(guesses, sum)

    guesses = lapply(ps, function(p) (values > p) & !truth)
    fp = lapply(guesses, sum)

    tpr = unlist(tp)/hits
    fpr = unlist(fp)/misses
    
    points(fpr, tpr, col = 'green')
    
  }
  
  title(main = paste('Pairwise Correlation Data, N =', ns[i]),
        outer = TRUE)
  
  dev.off()
}
}

plot.pairwise('correlated-pairs')
plot.pairwise('correlated-halves')

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

out.dir = paste(out.dir, 'anova/')

file.base = 'simple-anova'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'X + Y = Z')
dev.off()

file.base = 'simple-anova-omitted'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'X + W = Z')
dev.off()

#file.base = 'simple-anova-mixture'
#png(paste(out.dir, file.base, '-results.png'))
#plot.anova(file.base, 'X + Y = Z, X,Y ~ mixture')
#dev.off()

file.base = 'anova-1'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'X + Y + XY = Z')
dev.off()

file.base = 'anova-2'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'X + XY = Z')
dev.off()

file.base = 'anova-3'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'XY = Z')
dev.off()

file.base = 'anova-1-omitted'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'X + W + XW= Z')
dev.off()

file.base = 'anova-2-omitted'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'X + XW = Z')
dev.off()

file.base = 'anova-3-omitted'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'XW = Z')
dev.off()

#file.base = 'anova-1-mixture'
#png(paste(out.dir, file.base, '-results.png'))
#plot.anova(file.base, 'X + Y + XY = Z, X,Y ~ mixture')
#dev.off()

#file.base = 'anova-2-mixture'
#png(paste(out.dir, file.base, '-results.png'))
#plot.anova(file.base, 'X + XY = Z, X,Y ~ mixture')
#dev.off()

#file.base = 'anova-3-mixture'
#png(paste(out.dir, file.base, '-results.png'))
#plot.anova(file.base, 'XY = Z, X,Y ~ mixture')
#dev.off()

file.base = 'anova-correlated-1'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'X + Y + XY = Z, X,Y ~ correlated')
dev.off()

file.base = 'anova-correlated-2'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'X + XY = Z, X,Y ~ correlated')
dev.off()

file.base = 'anova-correlated-3'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'XY = Z, X,Y ~ correlated')
dev.off()

file.base = 'anova-correlated-1-omitted'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'X + W + XW = Z, X,Y ~ correlated')
dev.off()

file.base = 'anova-correlated-2-omitted'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'X + XW = Z, X,Y ~ correlated')
dev.off()

file.base = 'anova-correlated-3-omitted'
png(paste(out.dir, file.base, '-results.png'))
plot.anova(file.base, 'XW = Z, X,Y ~ correlated')
dev.off()
