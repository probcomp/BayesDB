#ifndef GUARD_view_h
#define GUARD_view_h


#include <string>
#include <map>
#include <vector>
//
#include "utils.h"
#include "Cluster.h"
#include "numerics.h"

//must forward declare
template <class T> class Cluster;

class View {
 public:
 View(int NUM_COLS, double CRP_ALPHA): num_cols(NUM_COLS), crp_alpha(CRP_ALPHA) {};
  double get_num_vectors() const;
  double get_num_cols() const;
  double get_score() const;
  //
  double insert_row(std::vector<double> vd, int cluster_idx, int row_idx); 
  double remove_row(std::vector<double> vd, int cluster_idx, int row_idx); 
  double calc_cluster_vector_logp(std::vector<double> vd, int cluster_idx) const;
  std::vector<double> calc_cluster_vector_logps(std::vector<double> vd) const;
  Cluster<double> copy_cluster(int cluster_idx) const;
  int get_cluster_location(int row_idx) const;
  // double score_test_set(std::vector<std::vector<double> > test_set) const;
  /* void transition_z(); */
  /* void transition_crp_alpha(); */
  /* void transition_data_hypers(); */
  void print();
 private:
  double crp_alpha;
  double score;
  int num_clusters;
  int num_vectors;
  int num_cols;
  /* std::map<std::string, double> data_hypers; */
  std::map<int, int> cluster_lookup;
  std::vector<Cluster<double> > clusters;
  Cluster<double>& get_new_cluster();
  Cluster<double>& get_cluster(int cluster_idx);
  std::vector<int> get_cluster_counts();
  /* void transition_vector(); */
  double get_data_score();
  double get_crp_score();
  /* double get_data_hyper_score(); */
  /* std::vector<double> get_vector_data_logps(std::vector<double>); */
  /* std::vector<double> get_vector_crp_logps(std::vector<double>); */
};


#endif //GUARD_view_h
