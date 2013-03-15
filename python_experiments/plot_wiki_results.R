datasets = c(0:6, 14:20)

png('../../plots/wiki-results.png',width=700,200)

par(mfrow = c(3,7), mai = c(0.1,0.1,0.1,0.1),
        mgp = c(0,0.5,0))

par(mfrow = c(2,7))

for(i in datasets) {

  data = read.csv(paste('../../crosscat-out/wiki-i-',i,'.csv',sep=''),
           header = F)

  plot.new()
  plot.window(
    xlim = range(data[,1]),
    ylim = range(data[,2]))

  points(data, pch = '.')

}

dev.off()

png('../../plots/wiki-data.png',width=700,200)

par(mfrow = c(3,7), mai = c(0.1,0.1,0.1,0.1),
        mgp = c(0,0.5,0))

par(mfrow = c(2,7))

for(i in datasets) {

  data = read.csv(paste('../../data/wiki-i-',i,'-data.csv',sep=''),
           header = F)

  plot.new()
  plot.window(
    xlim = range(data[,1]),
    ylim = range(data[,2]))

  points(data, pch = '.')

}

dev.off()
