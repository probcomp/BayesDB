library(mvtnorm)

write.data <- function(data, k) {
  print(cor(data[,1], data[,2]))

  plot.new()
  if(k <= 13) {
    plot.window(
      xlim = c(-3,3),
      ylim = c(-3,3))
  } else {
    plot.window(
      xlim = range(data[,1]),
      ylim = range(data[,2]))
  }
  points(data, pch = '.')
  name = paste('../../data/wiki-i-',k,'-data.csv',sep='')
  labels = paste('../../data/wiki-i-',k,'-labels.csv',sep='')
  write.table(data, file = name, row.names=F, col.names=F,
              sep = ',')
  write.table(matrix(rep('normal_inverse_gamma',2),1,2),
              file = labels,
              quote = F, row.names = F, col.names = F,
              sep = ',')
}

png('../../plots/wiki-data.png',width=700,300)

par(mfrow = c(3,7), mai = c(0.1,0.1,0.1,0.1),
        mgp = c(0,0.5,0))

n = 500

k = 0

corrs = c(1, 0.8, 0.4, 0.0, -0.4, -0.8, -1)
mean = c(0,0)
for(corr in corrs) {
  
  sigma = matrix(c(1,corr,corr,1),2,2)
  
  data = rmvnorm(n, mean, sigma)

  write.data(data, k)
  
  k = k + 1
}

slopes = c(1, 2/3, 1/3, 0, -1/3, -2/3, -1)
for(slope in slopes) {
  
  data[,1] = rnorm(n)
  data[,2] = slope*data[,1]

  write.data(data, k)
  
  k = k + 1
}


data[,1] = 2*runif(n) - 1
data[,2] = cos(1.6*pi*data[,1]) + 1.5*runif(n) 
write.data(data, k)
k = k + 1

theta = pi/3
rot = matrix(c(cos(theta), sin(theta), -sin(theta), cos(theta)),
  2,2)
data[,1] = 2*runif(n) - 1
data[,2] = 2*runif(n) - 1
data = data%*%rot
write.data(data, k)
k = k + 1

theta = pi/4
rot = matrix(c(cos(theta), sin(theta), -sin(theta), cos(theta)),
  2,2)
data[,1] = 2*runif(n) - 1
data[,2] = 2*runif(n) - 1
data = data%*%rot
write.data(data, k)
k = k + 1

data[,1] = 2*runif(n) - 1
data[,2] = data[,1]^2 + runif(n) 
write.data(data, k)
k = k + 1

data[,1] = 2*runif(n) - 1
assign = rbinom(n, 1, 0.5)
data[,2] = assign*(data[,1]^2 + runif(n)/2) +
  (1 - assign)*(-data[,1]^2 - runif(n)/2)
write.data(data, k)
k = k + 1

theta = 2*pi*runif(n)
r = rnorm(n, 1, 0.1)
data[,1] = r*cos(theta)
data[,2] = r*sin(theta)
write.data(data, k)
k = k + 1

assign = rmultinom(n, 1, rep(1/4,4))
loc = matrix(c(1,1,1,-1,-1,1,-1,-1), 2, 4)
data = t(loc%*%assign) + rnorm(2*n,0,0.3)
write.data(data, k)
k = k + 1


dev.off()
