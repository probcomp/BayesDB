data = read.csv('../../data/dha-raw.csv')
locs = data[,1]
data = data[,2:ncol(data)]
names = colnames(data)

results = read.csv('../../crosscat-results/dha-results.csv')
results = results[order(results[,3], decreasing=T),]

mine = read.csv('../../mine/dha-results.csv')

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
