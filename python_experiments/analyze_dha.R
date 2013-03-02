library(fields)
library(RColorBrewer)

data = read.csv('../../data/dha-raw.csv')
locs = data[,1]
data = data[,2:ncol(data)]
names = colnames(data)

results = read.csv('../../crosscat-results/dha-results.csv')
results = results[order(results[,3], decreasing=T),]

mine = read.csv('../../mine/dha-results.csv')

z.mat = read.csv('../../crosscat-results/dha-z-results.csv',
  header=F)
z.mat = as.matrix(z.mat + t(z.mat))
diag(z.mat) = 1

compare = which(colnames(data) == "QUAL_SCORE")

inds = (results[,'i'] == compare)| (results[,'j'] == compare)

est.r2 <- function(mi) {
  sqrt(1 - exp(-2*mi*(mi >= 0)))
}

strength = aggregate(est.r2(results[inds,'mutual_info']),
  by = list(results[inds,'i'], results[inds,'j']),
  mean)

reps = length(unique(results[,'rep']))
certainty = aggregate(results[inds,'mutual_info'],
  by = list(results[inds,'i'], results[inds,'j']),
  function(x) sum(x > 0)/reps)

inds = (mine[,1] == compare)| (mine[,2] == compare)

mine.strength = mine[inds,][order(mine[inds,1], mine[inds,2]),3]

plot.mat = cbind(mine.strength,
  z.mat[compare,-compare],
  certainty[[3]],
  strength[[3]])

png('../../plots/dha-comparison.png')

par(mar=c(2.1,5.1,4.1,4.1))
image(plot.mat,axes=F,col='transparent')
axis(2,at=seq(0,1,l=ncol(plot.mat)),
     labels=c(
       'MIC',
       'Z-Certainty',
       'Certainty',
       'Strength'))
image.plot(plot.mat,add=T,legend.mar=3.1,col = pal(10))

dev.off()

par(mfrow = c(3,3))
for(i in 1:9) {
  col1 = mine[i,1]
  col2 = mine[i,2]
  plot(data[,col1], data[,col2],
       xlab = names[col1], ylab = names[col2])
}

par(mfrow = c(3,3))
for(i in 1:9) {
  col1 = results[i,1]
  col2 = results[i,2]
  plot(data[,col1], data[,col2],
       xlab = names[col1], ylab = names[col2])
}
