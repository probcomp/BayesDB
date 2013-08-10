import sys
import csv
import os
#
import numpy
#
import tabular_predDB.python_utils.xnet_utils as xu

def parse_to_csv(filename, outfile='parsed_convergence.csv'):
   #drive, path = os.path.splitdrive(filename)
   #outpath, file_nameonly = os.path.split(path)
    
    with open(filename) as fh:
        lines = []
        for line in fh:
            lines.append(xu.parse_hadoop_line(line))
          
    fh.close()
    header = ['experiment', 'num_rows', 'num_cols', 'num_clusters', 'num_views', 'num_steps','block_size','ari_views', 'ari_table']
   
    reduced_lines = map(lambda x: x[1], lines)

    with open(outfile,'w') as csvfile:
        csvwriter = csv.writer(csvfile,delimiter=',')
	csvwriter.writerow(header)
        for line in lines:
            tmp_list = [int(line[0]),line[1]['num_rows'],line[1]['num_cols'], \
                            line[1]['num_views'],line[1]['num_clusters'],\
                            line[1]['n_steps'],line[1]['block_size']]
            csvwriter.writerow(tmp_list+ line[1]['ari_views']+line[1]['ari_table'])

    csvfile.close()
      
