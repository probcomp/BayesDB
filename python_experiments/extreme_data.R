n = 50
w = rnorm(n, 1000, 200)
x = w + rnorm(n, 0, 10)
y = rbinom(n, 1, 0.05)
z = 10*rbinom(n, 1, 0.05)

data = data.frame(w,x,y,z)

write.table(data,
            file = '../../data/extreme-data.csv',
            quote = F, sep = ',', row.names = F,
            col.names = F,
            na = '')
write.table(matrix(rep('normal_inverse_gamma',ncol(data)),1,
                   ncol(data)),
            file = '../../data/extreme-labels.csv',
            quote = F, sep = ',', row.names = F,
            col.names = F)
