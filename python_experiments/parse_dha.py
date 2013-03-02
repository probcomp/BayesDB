from crosscat_helper import *

out_file = '../../crosscat-out/dha-out.txt'
f = open(out_file)
result = f.read()
f.close()

values = parse_text(result, 'correlation')

f = open('../../crosscat-results/dha-results.csv', 'w')
f.write('i,j,mutual_info\n')
for i in range(len(values)):
    f.write(values[i] + '\n')
f.close()
