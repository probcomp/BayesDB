#include <iostream>

#include "State.h"
#include "utils.h"
#include "constants.h"

#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>

typedef boost::numeric::ublas::matrix<double> matrixD;
using namespace std;

int main(int argc, char** argv) {
  cout << endl << "test_state: Hello World!" << endl;

  // load some data
  matrixD data;
  string filename = "SynData2.csv";
  // string filename = "analyze_2d/ring_data.csv";
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
  State s = State(data, global_col_types, global_col_multinomial_counts, global_row_indices, global_column_indices, 11);

  cout << "start X_D" << endl << s.get_X_D() << endl;
  int num_views = s.get_num_views();
  cout << "s.num_views: " << num_views << endl;
  for(int view_idx=0; view_idx<num_views; view_idx++) {
    View &v = s.get_view(view_idx);
    cout << "view idx " << view_idx << ": ";
    v.print();
  }

  for(int i=0;i<200;i++) {
    cout << "transition #: " << i << endl;
    s.transition(data);
    cout << "FLAG: s.column_crp_alpha: " << s.get_column_crp_alpha() << endl;
    cout << "FLAG: s.num_views: " << s.get_num_views() << endl;
  }

  num_views = s.get_num_views();
  for(int view_idx=0; view_idx<num_views; view_idx++) {
    View &v = s.get_view(view_idx);
    cout << "view_idx " << view_idx << ": " << endl;
    v.print();
  }
  
  cout << "end X_D" << endl << s.get_X_D() << endl;
  cout << endl << "test_state: Goodbye World!" << endl;
}
