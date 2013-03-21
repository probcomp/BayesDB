import argparse
#
import numpy
#
import tabular_predDB.python_utils.data_utils as du
from tabular_predDB.jsonrpc_http.Engine import Engine


# parse input
parser = argparse.ArgumentParser()
parser.add_argument('--filename', default='testdata_kiva100files_mod.csv',
                    type=str)
parser.add_argument('--inf_seed', default=0, type=int)
parser.add_argument('--gen_seed', default=0, type=int)
parser.add_argument('--num_transitions', default=1000, type=int)
parser.add_argument('--N_GRID', default=31, type=int)
parser.add_argument('--max_rows', default=500, type=int)
args = parser.parse_args(['--filename', '../KivaAnalysis/testdata_kiva100files_mod.csv'])
#
filename = args.filename
inf_seed = args.inf_seed
gen_seed = args.gen_seed
num_transitions = args.num_transitions
N_GRID = args.N_GRID
max_rows = args.max_rows


continuous_labels = set([
        'Lender Country GDP Score', 'Lender Join Date', 'Lender Loan count',
        'Lender Invitee Count', 'Borrower Country GDP Score',
        'Number of Borrowers', 'Funded Amount', 'Loan Amount'
        ])
multinomial_labels = set([
        'Lender Country Label', 'Lender Occupation Label', 'Lender URL Flag',
        'Borrower Country Label', 'Field Partner ID', 'Loan ID',
        'Loan Sector Label', 'Loan Status Label'
        ])

T, M_r, M_c, header = du.all_continuous_from_file(filename, max_rows, gen_seed)
is_multinomial = [label in multinomial_labels for label in header]
multinomial_column_indices = numpy.nonzero(is_multinomial)[0]
T, M_c = du.convert_columns_to_multinomial(T, M_c,
                                           multinomial_column_indices)

kernel_list = None
n_steps = 2
c, r, max_iterations, max_time = None, None, None, None
engine = Engine()
M_c, M_r, X_L, X_D = engine.initialize(M_c, M_r, T)
X_L, X_D = engine.analyze(M_c, T, X_L, X_D, kernel_list, n_steps, c, r, max_iterations, max_time)
