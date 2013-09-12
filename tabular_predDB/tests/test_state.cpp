/*
* Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
*
*   Licensed under the Apache License, Version 2.0 (the "License");
*   you may not use this file except in compliance with the License.
*   You may obtain a copy of the License at
*
*       http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*   See the License for the specific language governing permissions and
*   limitations under the License.
*/
#include <iostream>
//
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>
//
#include "State.h"
#include "utils.h"
#include "constants.h"
//
typedef boost::numeric::ublas::matrix<double> matrixD;
using namespace std;


int n_iterations = 10;
string filename = "T.csv";


// passing in a State is dangerous, if you don't pass in a reference, memory will be deallocated
// and bugs/segfaults will occur
void print_state_summary(const State &s) {
    cout << "s.num_views: " << s.get_num_views() << endl;    
    for(int j=0;j<s.get_num_views(); j++) {
	    cout << "view " << j;
	    cout << " row_paritition_model_counts: " << s.get_row_partition_model_counts_i(j) << endl;
    }
    cout << "s.column_crp_score: " << s.get_column_crp_score();
    cout << "; s.data_score: " << s.get_data_score();
    cout << "; s.score: " << s.get_marginal_logp();
    cout << endl;
    return;
}

int main(int argc, char** argv) {
  cout << endl << "test_state: Hello World!" << endl;


  // load some data
  matrixD data;
  LoadData(filename, data);
  cout << "data is: " << data << endl;
  int num_rows = data.size1();
  int num_cols = data.size2();

  // create the objects to test
  vector<int> global_row_indices = create_sequence(data.size1());
  vector<int> global_column_indices = create_sequence(data.size2());
  vector<string> global_col_types;
  vector<int> global_col_multinomial_counts;
  for(int i=0; i<global_column_indices.size(); i++) {
    global_col_types.push_back(CONTINUOUS_DATATYPE);
    global_col_multinomial_counts.push_back(0);
  }
  State s = State(data, global_col_types,
		  global_col_multinomial_counts,
		  global_row_indices,
		  global_column_indices);


  cout << "start X_D" << endl << s.get_X_D() << endl;
  // cout << "State:" << endl << s << endl;

  vector<int> empty_int_v;
  for(int i=0; i<n_iterations; i++) {
    cout << "transition #: " << i << endl;
    s.transition_column_crp_alpha();
    s.transition_column_hyperparameters(empty_int_v);
    s.transition_row_partition_hyperparameters(empty_int_v);
    s.transition_features(data, empty_int_v);
    s.transition_row_partition_assignments(data, empty_int_v);
    // s.transition(data);
    print_state_summary(s);
  }


  // cout << "FINAL STATE" << endl;
  // cout << s << endl;
  cout << "end X_D" << endl << s.get_X_D() << endl;


  cout << endl << "test_state: Goodbye World!" << endl;
}
