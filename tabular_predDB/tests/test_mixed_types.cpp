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
#include <map>
#include <vector>
//
#include "utils.h"
#include "State.h"
#include "View.h"
#include "MultinomialComponentModel.h"
#include "ContinuousComponentModel.h"

#include <iostream>

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>

typedef boost::numeric::ublas::matrix<double> matrixD;
using namespace std;

int main() {
  cout << "test_mixed_types: Hello World" << endl;

  int multinomial_col_idx = 0;
  matrixD data;
  LoadData("SynData2.csv", data);
  int num_rows = data.size1();
  int num_cols = data.size2();
  map<int, int> value_counts;
  for(int row_idx=0; row_idx<num_rows; row_idx++) {
    int int_value = (int)data(row_idx, multinomial_col_idx);
    data(row_idx, 0) = int_value;
    if(!in(value_counts, int_value)) {
      value_counts[int_value] = 0;
    } else {
      value_counts[int_value]++;
    }
  }
  cout << data << endl;

  vector<string> GLOBAL_COL_DATATYPES;
  GLOBAL_COL_DATATYPES.push_back("symmetric_dirichlet_discrete");
  vector<int> GLOBAL_COL_MULTINOMIAL_COUNTS;
  GLOBAL_COL_MULTINOMIAL_COUNTS.push_back(value_counts.size());
  for(int i=1; i<num_cols; i++) {
    GLOBAL_COL_DATATYPES.push_back("normal_inverse_gamma");
    GLOBAL_COL_MULTINOMIAL_COUNTS.push_back(0);
  }
  vector<int> global_row_indices = create_sequence(num_rows);
  vector<int> global_col_indices = create_sequence(num_cols);
  State s(data, GLOBAL_COL_DATATYPES, GLOBAL_COL_MULTINOMIAL_COUNTS,
	  global_row_indices, global_col_indices);

  for(int i=0; i<3; i++) {
    cout << "transition " << i << endl;
    s.transition(data);
    cout << s << endl;
    cout << endl;
    cout << endl;
  }

  cout << "test_mixed_types: Goodbye World" << endl;

}
