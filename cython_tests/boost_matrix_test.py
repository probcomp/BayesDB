import boost_matrix_test as bmt


num_rows = 500
num_cols = 5

p_matrix = bmt.p_matrix(num_rows, num_cols)
print p_matrix
print "p_matrix.get(0, 0):", p_matrix.get(0, 0)
p_matrix.set(0,0, -1.)
print "p_matrix.get(0, 0):", p_matrix.get(0, 0)
