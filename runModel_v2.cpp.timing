
#include <stdio.h>
#include <stdlib.h>
#include <math.h>


#include <iostream>     // cout, endl
#include <iomanip>
#include <fstream>      // fstream
#include <vector>
#include <string>
#include <algorithm>    // copy
#include <iterator>     // ostream_operator
#include <ctime>
#include <map>

#include <boost/math/constants/constants.hpp>
#include <boost/assign/std/vector.hpp>
#include <boost/tokenizer.hpp>
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/matrix_proxy.hpp>
#include <boost/numeric/ublas/io.hpp>
#include <boost/random/mersenne_twister.hpp>
#include <boost/random/normal_distribution.hpp>
#include <boost/random/variate_generator.hpp>
#include <boost/program_options.hpp>

#include "DateTime.h"

using namespace std;
using namespace boost;
using namespace boost::numeric::ublas;

typedef boost::numeric::ublas::vector<double> VectorD;
typedef boost::numeric::ublas::matrix<double> MatrixD;

class State;


void MainLoop(State& state);
void SaveResults(const std::vector<State>& samples);

void SaveMatrix(const MatrixD& M, std::string filename);
void SetaRange(State& state);
void SetCrpParameterRanges(State& state);
void SetMuBetaRanges(State& state);


MatrixD Concat(const MatrixD& M1, const MatrixD& M2);
void Add(MatrixD& M , double val);
void Print(const MatrixD& M, const std::string msg);
void PrintV(const std::vector<double>& V, const std::string msg);
void LoadData(std::string file, MatrixD&);
MatrixD linspace(double x1, double x2, int num_elements);
MatrixD ones(int nrows, int ncols);
MatrixD zeros(int nrows, int ncols);
MatrixD init_matrix(int nrows, int ncols, double vals);
double sum(const MatrixD& M);
MatrixD cumsum(const MatrixD& M, int dim = 2);
MatrixD cumsum2(const std::vector<double>& V);
double mean(const MatrixD& M);
int GetFirstIndex(const MatrixD& M1, double r);
int length(const MatrixD& M);
MatrixD unique(const MatrixD& M);
int CountInstances(const MatrixD& M, int val);
MatrixD StripZeros(const MatrixD& M);
MatrixD gammaln(const MatrixD M);
MatrixD Exp(const MatrixD& M);
MatrixD init_matrix_mti(int start, int end);
MatrixD setdiff(const MatrixD& M1 , const MatrixD& M2);
MatrixD get_row(const MatrixD M, int i);
MatrixD find_indexes(const MatrixD M, int val);
////////////////////////////////////////////////
// utility function for use with running in gdb
double get_element(MatrixD M, int i, int j);

///////////////////////////////////////////////////////
// functions from m file
MatrixD sample_partition(int n, double gamma);
State drawSample(State& state, int lag);
State sampleHyperParams(State& state); 
State sampleKinds(State& state);
State sampleCategories(State& state);
State sampleCategoriesK(State& state, int K, int O);
double crp(const MatrixD& cats, double gamma);
double prob_of_partition_via_counts(MatrixD& ns, double gama);
int chooseState(const MatrixD& logP); 
double logsumexp(const MatrixD& a , int dim);
void jumpParam(State& state, int f, double& ng_mu, double& NG_a,
	       double& NG_b, double& NG_k);
double NG(const MatrixD& data, double mu0, double k0, double a0, double b0);
double sampleMu(const State& state, int f, const MatrixD c, int thisK);
double sampleA(const State& state, int f, const MatrixD c, int thisK);
double sampleB(const State& state, int f, const MatrixD c, int thisK);
double sampleK(const State& state, int f, const MatrixD c, int thisK);
double scoreFeature(State& state, double f);
double scoreObject(State& state, int K , int O);
double NG_cat(const MatrixD& data, double newData, double mu0, double k0, double a0, double b0);

class RandomNumberGen
{
public:
  RandomNumberGen() : _engine(0), _dist(_engine)
  //RandomNumberGen() : _engine(std::time_t(0)), _dist(_engine)
  {
  }

  //////////////////////////////////
  // return a random real between 
  // 0 and 1 with uniform dist
  double next()
  {
    return _dist();
  }

  //////////////////////////////
  // return a random int bewteen 
  // zero and max - 1 with uniform
  // dist if called with same max
  int nexti(int max)
  {
    double D = (double)max;
    return (int)std::floor((next() * D));
  }

  void set_seed(std::time_t seed) {
    _engine.seed(seed);
  }
protected:
   // Mersenne Twister
  boost::mt19937  _engine;
  // uniform Distribution
  boost::uniform_01<boost::mt19937> _dist;
};


class State
{
public:
  State() {}
  ~State() {}

  int F;
  int O;
  MatrixD f;
  MatrixD o;
  MatrixD paramPrior;
  MatrixD cumParamPrior;
  MatrixD paramRange;
  MatrixD crpKRange;
  MatrixD crpCRange;
  MatrixD kRange;
  MatrixD aRange;
  MatrixD muRange;
  MatrixD bRange;
  double crpPriorK;
  double crpPriorC;
  MatrixD NG_a;
  MatrixD NG_k;
  MatrixD NG_b;
  MatrixD NG_mu;    
  MatrixD data;

};


class GlobalParameters
{
public:
  GlobalParameters() : PI(boost::math::constants::pi<double>())
  {
  }
  const double PI;
  // set some initial vars
  int nChains;
  int nSamples;
  int burnIn;
  int lag;
  int bins;
  string dataFile;
  RandomNumberGen Rand;
};

GlobalParameters GP;

int main(int argc, char** argv)
{

  string default_dataFile = "SynData2";
  std::time_t default_seed = 0;
  int default_nChains = 1;
  int default_nSamples = 40;
  int default_burnIn = 500;
  int default_lag = 10;
  int default_bins = 31;
  //
  std::time_t seed;

  //parse some arguments
  namespace po = boost::program_options;
  po::options_description desc("Options");
  desc.add_options()
    ("help,h", "produce help message")
    ("seed", po::value<std::time_t>(&seed)->default_value(default_seed), "set inference seed")
    ("dataFile", po::value<string>(&GP.dataFile)->default_value(default_dataFile), "set data to run inference on")
    ("nChains", po::value<int>(&GP.nChains)->default_value(default_nChains), "set number of inference chains to run")
    ("nSamples", po::value<int>(&GP.nSamples)->default_value(default_nSamples), "set number of samples to draw (@lag)")
    ("burnIn", po::value<int>(&GP.burnIn)->default_value(default_burnIn), "set number of burn in iterations")
    ("lag", po::value<int>(&GP.lag)->default_value(default_lag), "set number of iterations per sample")
    ("bins", po::value<int>(&GP.bins)->default_value(default_bins), "set number of bins in hyper inference")
    ;
  po::variables_map vm;
  try {
    po::store(po::parse_command_line( argc, argv, desc ), vm);
    po::notify( vm );
    if ( vm.count("help") ) {
      std::cout << desc << "\n";
      exit(0);
    }
  } catch ( const boost::program_options::error& e ) {
    std::cerr << e.what() << std::endl;
  }

  using namespace boost::assign;

  // set GP seed from command line argument
  GP.Rand.set_seed(seed);

  cout << "dataFile = " << GP.dataFile << endl;
  cout << "seed = " << seed << endl;

  State state;

 
  // load data file
  LoadData(GP.dataFile + ".csv", state.data);

  // num cols
  state.F = state.data.size2();
  // num rows
  state.O = state.data.size1();

  // parameters
  MatrixD x = linspace(0.03, 0.97, GP.bins);

  state.paramPrior = ones(1, x.size2());
  state.paramPrior = state.paramPrior / sum(state.paramPrior);
  state.cumParamPrior = cumsum(state.paramPrior);
  MatrixD y = -x + ones(1, x.size2());
  state.paramRange = element_div(x, y);
 
  // set CRP parameter ranges
  SetCrpParameterRanges(state);

  // set k parameter range
  state.kRange = state.crpCRange;

  // set 'a' range to n/2
  SetaRange(state);

  // set mu and beta ranges
  SetMuBetaRanges(state);

  MainLoop(state);
  
  return 0;
  
  
}


void MainLoop(State& state)
{
  std::vector<State> samples;
  int nc = 1;
  for(; nc <= GP.nChains; nc++)
    {
      cout<< "nc = " << nc << endl;
      // initialize parameters randomly
      int index = GetFirstIndex(state.cumParamPrior, GP.Rand.next());
      state.crpPriorK = state.crpKRange(0,index);
      index = GetFirstIndex(state.cumParamPrior, GP.Rand.next());
      state.crpPriorC = state.crpCRange(0,index);
      
      int i;
      state.NG_a.resize(1,state.F);
      state.NG_k.resize(1,state.F);
      state.NG_b.resize(1,state.F);
      state.NG_mu.resize(1,state.F);

      for(i = 0; i < state.F; i++)
	{
	  index = GetFirstIndex(state.cumParamPrior, GP.Rand.next());
	  state.NG_a(0,i) = state.aRange(0, index);

	  index = GetFirstIndex(state.cumParamPrior, GP.Rand.next());
	  state.NG_k(0,i) = state.kRange(0, index);
	  
	  index = GetFirstIndex(state.cumParamPrior, GP.Rand.next()); 
	  state.NG_b(0,i) = state.bRange(i, index);
	  
	  index = GP.Rand.nexti(state.muRange.size2());
	  state.NG_mu(0,i) = state.muRange(i, index);

	}


      // initialize state
      // state.f stores a partition of features; each element is the
      // corresponding kind the feature is assigned to. It is an
      // integer array of size 1 x state.F
    
      state.f = sample_partition(state.F, state.crpPriorK);

      //state.o stores a partition of objects for each category of
      // features. It is an integer matrix of size kinds x state.O where
      // kinds = max(staet.f).
    

      int max = (int)*std::max_element(state.f.begin2(), state.f.end2());
      state.o.resize(max, state.O);
      
      for(i = 0; i < max; i++)
      	{
      	  MatrixD Opart = sample_partition(state.O, state.crpPriorC);
      	  project(state.o, range(i, i+1), range(0, Opart.size2())) = Opart;
      	}

      // runModel
      Timer T(true);

      // burn-in
      samples.push_back(drawSample(state, GP.burnIn));

      //      samples{length(samples)+1} = drawSample(state, burnIn); 
      cout <<" t1 = " << T.GetElapsed() << endl;
      // storing MCMC samples
      int ns;
      for(ns=2; ns <= GP.nSamples; ns++)
      	{
	  // only store every 'lag' samples
	  cout << "ns = " << ns << endl;
      	  samples.push_back(drawSample(samples[samples.size() - 1], GP.lag));
      	  cout << "t2 = " <<  T.GetElapsed() << endl;
      	}  
    }

  SaveResults(samples);

}


void SaveResults(const std::vector<State>& samples)
{
  string filename = "crossCatNG_" + GP.dataFile + " (" + DateTime::GetDateTimeStr() + ")";

  ofstream out(filename.c_str()); 
  if(!out) 
    { 
      cout << "Cannot open file.\n"; 
      return; 
    } 

  out << "nChains = " <<  GP.nChains << endl;
  out << "nSamples = " <<  GP.nSamples << endl;
  out << "burnIn = " <<  GP.burnIn << endl;
  out << "lag = " <<  GP.lag << endl;

  out << endl;

  int i;
  for(i = 0; i < samples.size() ;i++)
    {
      State state = samples[i];
      out << "State"<<i<<endl;
      out << "F = " << state.F << endl;
      out << "O = " << state.O << endl;
      out << "f = " << state.f << endl;
      out << "o = " << state.o << endl;
      out << "paramPrior = " << state.paramPrior << endl;
      out << "cumParamPrior = " << state.cumParamPrior << endl;
      out << "paramRange = " << state.paramRange << endl;
      out << "crpKRange = " << state.crpKRange << endl;
      out << "crpCRange = " << state.crpCRange << endl;
      out << "kRange = " << state.kRange << endl;
      out << "aRange = " << state.aRange << endl;
      out << "muRange = " << state.muRange << endl;
      out << "bRange = " << state.bRange << endl;
      out << "crpPriorK = " << state.crpPriorK << endl;
      out << "crpPriorC = " << state.crpPriorC << endl;
      out << "NG_a = " << state.NG_a << endl;
      out << "NG_k = " << state.NG_k << endl;
      out << "NG_b = " << state.NG_b << endl;
      out << "NG_mu = " << state.NG_mu << endl;
      out << endl << endl;
    }


    
  out.close();   
}

int len(MatrixD vector_matrix) {
  return vector_matrix.size2();
}


MatrixD get_cluster_counts(MatrixD state_o, MatrixD unique_f) {
  int num_views = unique_f.size2(); //state_o.size1();
  int num_objects = state_o.size2();
  MatrixD cluster_counts = boost::numeric::ublas::zero_matrix<double>(1, num_views);
  for(int unique_f_idx=0; unique_f_idx<num_views; unique_f_idx++) {
    int view_idx = unique_f(0, unique_f_idx);
    view_idx -= 1; //for matlab to c++ indexing
    MatrixD curr_o = project(state_o, boost::numeric::ublas::range(view_idx, view_idx+1),
			     boost::numeric::ublas::range(0, num_objects));
    cluster_counts(0, unique_f_idx) = len(unique(curr_o));
  }
  return cluster_counts;
}

void print_cluster_counts(MatrixD cluster_counts) {
  std::cout << cluster_counts(0,0);
  int num_counts = cluster_counts.size2();
  for(int count_idx=1; count_idx<num_counts; count_idx++) {
    int curr_count = cluster_counts(0,count_idx);
    std::cout << ";" << curr_count;
  }
}

void PrintM(const MatrixD& M, const std::string msg)
{
  cout << msg << " = " << endl << M << endl << endl;
}

State drawSample(State& state, int lag)
{ 
  int i;
  Timer my_T(true);
  for(i = 0; i < lag ; i++)
    {  
      cout << i << endl;
      //scoreState(state)
      State oldstate = state;

      // size the problem
      int start_num_views = len(unique(state.f));
      MatrixD start_num_clusters_per_view = get_cluster_counts(state.o, unique(state.f));
      // PrintM(state.o, "state.o, before");
      // PrintM(state.f, "state.f, before");
      my_T.Reset();

      // sample hyper parameters
      //cout << "SampleHyperParams" << endl;
      state = sampleHyperParams(state);

      // sample kinds
      //cout << "sampleKinds"<<endl;
      if (state.F > 1)
	{
	  //cout << "sampleKinds"<<endl;
	  state = sampleKinds(state);
	} 
      //sample categories
      //cout<<"sampleCategories"<<endl;
      state = sampleCategories(state);

      double elapsed_secs = my_T.GetElapsed();
      std::cout << "timing :: ";
      std::cout << state.F;
      std::cout << " , " << state.O;
      std::cout << " , " << start_num_views;
      std::cout << " , "; print_cluster_counts(start_num_clusters_per_view);
      std::cout << " , " << elapsed_secs << std::endl;
      // PrintM(state.o, "state.o, after");
      // PrintM(state.f, "state.f, after");
      1;
    }  

  return state;
}


State sampleHyperParams(State& state)
{
  // crpPrior kinds
  int len = length(state.crpKRange);
  MatrixD logP = zeros(1,len);
  int i;
  for(i = 0 ; i < len; i++)
    {
      state.crpPriorK = state.crpKRange(0,i); // assuming uniform prior
      logP(0,i) = crp(state.f, state.crpPriorK); // only need to look at kinds
    }
  
  // choose state
  int index = chooseState(logP); // normalize to probability distribution then take a sample
  state.crpPriorK = state.crpKRange(0,index); // 'this' denotes the particular sample drawn

  // crpPrior categories
  logP = zeros(1,length(state.crpCRange));
  int l = length(state.crpCRange);
  for(i = 0; i < l; i++)
    {
      
      state.crpPriorC = state.crpCRange(0,i);
      MatrixD u = unique(state.f);
      //Print(state.f, "state.f");
      //Print(u, "u");
      int j;
      for (j=0; j < u.size2(); j++)
	{
	  // DGREEN : subtract 1 for c++ indexing
	  int k = u(0,j) - 1;
	  if(k < 0)
	    {
	      Print(state.f, "state.f");
	      Print(u, "u");
	      exit(0);
	    }

	  MatrixD M = project(state.o, range(k, k+1), range(0, state.o.size2()));
	  logP(0,i) = logP(0,i) + crp(M, state.crpPriorC); // only need to look at categories
	}
    }

  // choose state
  index = chooseState(logP);
  state.crpPriorC = state.crpCRange(0,index);
  
  // sample feature params
  int f; 
  double NG_mu, NG_a, NG_b, NG_k; 
  for(f = 0; f < state.F; f++)
    {
      jumpParam(state, f, NG_mu, NG_a, NG_b, NG_k);
      state.NG_a(0,f) = NG_a;
      state.NG_b(0,f) = NG_b;
      state.NG_k(0,f) = NG_k;
      state.NG_mu(0,f) = NG_mu;      
    }
  
  return state;
}



void jumpParam(State& state, int f, double& NG_mu, double& NG_a,
	       double& NG_b, double& NG_k)
{
  // DGREEN : adjust for c++ indexing
  double thisK = state.f(0,f) - 1; // the feature category (view) associated with f
  MatrixD M; 
  M = project(state.o, range(thisK, thisK+1) , range(0, state.o.size2()));
  
  MatrixD c = unique(M); // object category assignment for thisK (view)  

  NG_mu = sampleMu(state, f, c, thisK);
  NG_a = sampleA(state, f, c, thisK);
  NG_b = sampleB(state, f, c, thisK);
  NG_k = sampleK(state, f, c, thisK);
  
}


double sampleMu(const State& state, int f, const MatrixD c, int thisK)
{
  int len1 = state.muRange.size2();
  MatrixD logP = zeros(1, len1);
  int i,j,k,l;
  int len2 = c.size2();
 
  for(i=0; i < len1 ; i++)
    { 
      for(j=0; j < len2 ; j++)
	{
	  // find indexes where state.o(thisK,:)  == c(0,j)
	  std::vector<int> indexes;
	  for(k=0; k < state.o.size2(); k++)
	    {
	      if(state.o(thisK,k) == c(0,j))
		indexes.push_back(k);
	    }
	  
	  // save to M
	  int sz = indexes.size();
	  MatrixD M(sz,1);
	  for(l=0;l < sz; l++)
	    {
	      M(l,0) = state.data(indexes[l], f);
	    }
	  
	  logP(0,i) = logP(0,i) + NG(M, state.muRange(f,i), state.NG_k(0,f), 
				     state.NG_a(0,f), state.NG_b(0,f));
	  	    
	}
    }
  
  // choose state
  int s = chooseState(logP);
  double NG_mu = state.muRange(f,s);
  return NG_mu;
}



double sampleK(const State& state, int f, const MatrixD c, int thisK)
{
  int len1 = state.kRange.size2();
  MatrixD logP = zeros(1, len1);
  int i,j,k,l;
  int len2 = c.size2();
 
  for(i=0; i < len1 ; i++)
    { 
      for(j=0; j < len2 ; j++)
	{
	  // find indexes where state.o(thisK,:)  == c(0,j)
	  std::vector<int> indexes;
	  for(k=0; k < state.o.size2(); k++)
	    {
	      if(state.o(thisK,k) == c(0,j))
		indexes.push_back(k);
	    }
	  
	  // save to M
	  int sz = indexes.size();
	  MatrixD M(sz,1);
	  for(l=0;l < sz; l++)
	    {
	      M(l,0) = state.data(indexes[l], f);
	    }
	  
	  logP(0,i) = logP(0,i) + NG(M, state.NG_mu(0,f), state.kRange(0,i), 
				     state.NG_a(0,f), state.NG_b(0,f));

	  logP(0,i) = logP(0, i) + log(state.paramPrior(0,i)); 
	  	    
	}
    }
  
  // choose state
  int s = chooseState(logP);
  double NG_k = state.kRange(0,s) + 1.0;
  return NG_k;
}

double sampleA(const State& state, int f, const MatrixD c, int thisK)
{
  int len1 = state.aRange.size2();
  MatrixD logP = zeros(1, len1);
  int i,j,k,l;
  int len2 = c.size2();
 
  for(i=0; i < len1 ; i++)
    { 
      for(j=0; j < len2 ; j++)
	{
	  // find indexes where state.o(thisK,:)  == c(0,j)
	  std::vector<int> indexes;
	  for(k=0; k < state.o.size2(); k++)
	    {
	      if(state.o(thisK,k) == c(0,j))
		indexes.push_back(k);
	    }
	  
	  // save to M
	  int sz = indexes.size();
	  MatrixD M(sz,1);
	  for(l=0;l < sz; l++)
	    {
	      M(l,0) = state.data(indexes[l], f);
	    }
	  
	  logP(0,i) = logP(0,i) + NG(M, state.NG_mu(0,f), state.NG_k(0,f), 
				     state.aRange(0,i), state.NG_b(0,f));

	  logP(0,i) = logP(0, i) + log(state.paramPrior(0,i)); 
	  	    
	}
    }
  
  // choose state
  int s = chooseState(logP);
  double NG_a = state.aRange(0,s);
  return NG_a;
}

double sampleB(const State& state, int f, const MatrixD c, int thisK)
{
  int len1 = state.bRange.size2();
  MatrixD logP = zeros(1, len1);
  int i,j,k,l;
  int len2 = c.size2();
 
  for(i=0; i < len1 ; i++)
    { 
      for(j=0; j < len2 ; j++)
	{
	  // find indexes where state.o(thisK,:)  == c(0,j)
	  std::vector<int> indexes;
	  for(k=0; k < state.o.size2(); k++)
	    {
	      if(state.o(thisK,k) == c(0,j))
		indexes.push_back(k);
	    }
	  
	  // save to M
	  int sz = indexes.size();
	  MatrixD M(sz,1);
	  for(l=0;l < sz; l++)
	    {
	      M(l,0) = state.data(indexes[l], f);
	    }
	  
	  logP(0,i) = logP(0,i) + NG(M, state.NG_mu(0,f), state.NG_k(0,f), 
				     state.NG_a(0,f), state.bRange(f,i));

	  logP(0,i) = logP(0, i) + log(state.paramPrior(0,i)) ;
	  	    
	}
    }
  
  // choose state
  int s = chooseState(logP);
  double NG_b = state.bRange(f,s);
  return NG_b;
}



 // the probability of data, given the priors under the normal-normal-gamma
  // model
  // this is based on kevin murphy's cheat sheet (NG.pdf)
  // data are assumed to be a vector
  // mu0, k0, a0, b0 are hyperparameters
double NG(const MatrixD& data, double mu0, double k0, double a0, double b0)
{

  double len = (double)length(data);
  double meanData = sum(data) / len;
  
  //     muN = (k0.*mu0 + len.*meanData) ./ (k0+len);
  double kN = k0 + len;
  double aN = a0 + len / 2.0;
  
  MatrixD diff1 = data;
  Add(diff1, -meanData);
  double diff2 = meanData - mu0;
  
  MatrixD M = element_prod(diff1, diff1); 
    
  double bN = b0 + 0.5 * sum(M) + (k0*len*(diff2*diff2)) / (2.0*(k0+len));
  
  double logProb = lgamma(aN) - lgamma(a0) + 
    log(b0) * a0 - log(bN) * aN + 
    log( (k0/kN) ) * 0.5 + 
    log( (2.0 *  GP.PI) ) *(-len/2.0);
  
  return logProb;
}





// Given unnormalized log probabilities, return a random sample 
int chooseState(const MatrixD& logP)
{
  MatrixD M = logP;
  Add(M, -logsumexp(M,2));
  MatrixD prob = Exp(M); // normalize to 1 given log-prob
  MatrixD cumprob = cumsum(prob); // CDF
  
  // find the first entry > rand
  double rand = GP.Rand.next();
  int i, result = 0;
  for(i = 0; i < cumprob.size2(); i++)
    {
      if(cumprob(0,i) > rand)
	{
	  result = i;
	  break;
	}
    }


  return result;
}


/////////////////////////////////////////////////////////////////////
// Returns log(sum(exp(a),dim)) while avoiding numerical underflow.
//  logsumexp(a, 2) will sum across columns instead of rows
// (ASSUMES row vector for now) users dim spec overridden  
double logsumexp(const MatrixD& a , int dim)
{
  MatrixD M = a;
  dim = 2;
  // subtract the largest in each column
  double y = *std::max_element(M.begin2(), M.end2());
  Add(M, -y);
  double res = y + log(sum(Exp(M)));
  return res;
}


//////////////////////////////////
// return matrix that applies
// exp operation on each element
MatrixD Exp(const MatrixD& M)
{
  int i,j;
  int m = M.size1();
  int n = M.size2();

  MatrixD result(m,n);

  for(i=0;i < m; i++)
    {
      for(j=0; j < n; j++)
	{
	  result(i,j) = ::exp(M(i,j));
	}
    }
  return result;
}


////////////////////////////////////////////////////////////////////
// this includes gibbs moves on features, and M-H move to propose new
// kinds
State sampleKinds(State& state)
{
  int f;

  for(f=0 ; f < state.F ; f++)
    {
      MatrixD k = unique(state.f);
      // first gibbs (only makes sense if there is more than one feature 
      // in this kind, and there is more than one kind)
      if((CountInstances(state.f,state.f(0,f)) > 1) && (length(k) > 1)) 
	{
	  std::vector<double> logP;
	  int j,K; 
	  int len_k = k.size2();
	  for(j=0 ; j < len_k ; j++)
	    {
	      K = k(0,j);
	      if(K == 0)
		{
		  cout<< "ERROR : K == 0" <<endl;
		}
	      state.f(0,f) = K;
	      
	      // crp
	      int sumF = CountInstances(state.f, K);
	      if(sumF > 1)
		{
		  double temp = (double)sumF - 1.0;
		  temp = temp / (state.F - 1 + state.crpPriorK); 
		  logP.push_back(log(temp));
		}
	      else
		{
		  logP.push_back(log(state.crpPriorK / (state.F - 1 + state.crpPriorK)));
		}

	      logP[logP.size() - 1] += scoreFeature(state, f); 
	    }

	  // create a matrix from logP 
	  MatrixD logP_M(1, logP.size());
	  for(j=0; j < logP.size() ; j++)
	    {
	      logP_M(0,j) = logP[j];
	    }
	  
	  int s = chooseState(logP_M);
	  int temp = k(0,s);
	  if(temp == 0)
	    {
	      cout << "ERROR temp = 0"<<endl;
	    }
	  state.f(0,f) = k(0,s);
	}
      
      
      // then MH choose new v old
      double cut = 0.5; // percent new
      State oldState = state;
      bool newOld = (GP.Rand.next() > cut);
      
      if( (length(k) == 1)  && newOld)
	{
	  continue;
	}
      
      double a;

      if(!newOld) // new
	{
	  //	  cout<< "new" << endl;
	  double logP_1, logP_2;
	  // sample partition

	  MatrixD M1 = init_matrix_mti(1, state.F + 1);
	  MatrixD M2 = setdiff(M1, k);

	  // newK gets first element
	  int newK = M2(0,0);
	  if(newK == 0)
	    {
	      cout<< "ERROR : newK = 0" << endl;
	    }

	  state.f(0,f) = newK;
	  // add new row to state.o if you have to
	  if(newK > state.o.size1())
	    {
	      MatrixD temp(newK, state.o.size2());
	      project(temp, range(0, newK - 1), range(0,state.o.size2())) = state.o;
	      state.o = temp;
	    }
	  
	  project(state.o, range(newK-1, newK), range(0,state.o.size2())) = sample_partition(state.O, state.crpPriorC);
	    
	  
	  // score new and score old
	  MatrixD M3 = project(state.o, range(newK-1, newK) , range(0, state.o.size2()));
	  logP_1 = scoreFeature(state, f) + // score feature
	    log( state.crpPriorK / (double)(state.F - 1 + state.crpPriorK)) + // new kind
	    crp(M3, state.crpPriorC); // new categories

	  double d1 = (double)CountInstances(oldState.f, oldState.f(0,f)) - 1.0;
	  logP_2 = scoreFeature(oldState, f) + // score feature
	    log( d1 / (double)(oldState.F - 1 + oldState.crpPriorK)); // new kind
	 

	  // M-H (t+1 -> t / t -> t+1)
	  double jump_1, jump_2;
	  if(CountInstances(oldState.f, oldState.f(0,f)) == 1) // deal with single feature kinds
	    {
	      // t + 1 -> t prob of new , prob of choosing cat t
	      MatrixD M1 = project(oldState.o, range(oldState.f(0,f) - 1, oldState.f(0,f)) , 
				   range(0, oldState.o.size2()));
	      jump_1 = log(cut) + crp(M1, state.crpPriorC);
	      // t -> t+1: prob of new, prob of choosing cat t+1
	      M1 = project(state.o, range(state.f(0,f) - 1, state.f(0,f)) , 
			   range(0, state.o.size2()));
	      jump_2 = log(cut) - crp(M1, state.crpPriorC);
	    }
	  else
	    {
	      // t+1 -> t: prob of old, prob of choosing kind @ t+1
	      jump_1 = log((1.0-cut)*(1.0/(double)length(unique(state.f))));
	      // t -> t+1: prob of new, prob of choosing cat t+1
	      MatrixD M1 = project(state.o, range(newK-1, newK) , range(0, state.o.size2()));
	      jump_2 = log(cut) + crp(M1,state.crpPriorC);
	    }

	  a = logP_1 - logP_2 + jump_1 - jump_2;
	}
      else // old
	{
	  // from 1 to length(k) 
	  int newK = 1 + GP.Rand.nexti(length(k));
	  if(newK == state.f(0,f))
	    {
	      continue;
	    }
	  
	  double logP_1, logP_2;
	  double temp = (double)(CountInstances(oldState.f, oldState.f(0,f)) - 1); 
	  logP_2 = scoreFeature(oldState,f) +
	    log( temp / (double)(oldState.F - 1 + oldState.crpPriorK) );

	  if(newK == 0)
	    {
	      cout<< "ERROR : newK == 0"<<endl;
	    }

	  state.f(0,f) = newK;
	  temp = (double)(CountInstances(state.f, state.f(0,f)));
	  logP_1 = scoreFeature(state,f) + 
	    log( temp / (double)(state.F - 1 + state.crpPriorK) ) ; 
	  
	  double jump_1, jump_2;
	  // M-H transition (t+1 -> t / t -> t+1)
	  if(CountInstances(oldState.f, oldState.f(0,f)) == 1) // single feature kind
	    {
	      // t+1 -> t: prob of new, prob of choosing cat t 
	      MatrixD M1 = project(oldState.o, range(oldState.f(0,f) - 1, oldState.f(0,f)),
				   range(0, oldState.o.size2()));
	      jump_1 = log(cut) + crp(M1, state.crpPriorC);
	     
	      // t -> t+1: prob of old, prob of choosing kind @ t
	      jump_2 = log((1.0-cut) * (1.0/ (double)(length(unique(oldState.f)))));
	      a = logP_1 - logP_2 + jump_1 - jump_2;
	    }
	  else
	    {
	      // t+1 -> t: prob of old, prob of choosing kind (same # kinds)
	      jump_1 = 0;
	      // t -> t+1: prob of old, prob of choosing kind (same # kinds)
	      jump_2 = 0;
	      a = logP_1 - logP_2 + jump_1 - jump_2;
	    }  
	}

      a = exp(a);
      if( a > GP.Rand.next())
	{
	  // state is adopted
	}
      else
	{
	  // return to old state
	  state = oldState;
	}
    }

  return state;
}


State sampleCategories(State& state)
{
  MatrixD k = unique(state.f);
  int i,O;
  for(i=0;i < k.size2() ; i++)
    {
      // DGREEN : adjust K or c++ indexing
      int K = k(0,i) - 1;
      for(O=0; O < state.O; O++)
	{
	  state = sampleCategoriesK(state, K, O);
	} 
    }

  return state;
}

// this executes gibbs sampling for a given kind
//
// K: (int) feature category (view) label
// O: (int) object index
State sampleCategoriesK(State& state, int K, int O)
{
  MatrixD M1 = project(state.o, range(K, K+1), range(0, state.o.size2()));
  MatrixD C = unique(M1);
  // choose a label for new category
  MatrixD M2 = init_matrix_mti(1, state.O);
  MatrixD empty = setdiff(M2, C);
  
  int max = *std::max_element(C.begin2(), C.end2());
  if((empty.size2() == 0) && (max == state.O))
    {
      // do nothing
    }
  else
    {
      C = Concat(C, project(empty, range(0,1), range(0, 1)));
    }

  MatrixD logP(1, C.size2());
  int i;
  for(i = 0 ; i < C.size2(); i++)
    {
      int c = C(0,i);
      state.o(K,O) = c;
      //     cout << "scoreObject" << endl;
      logP(0,i) = scoreObject(state, K, O);
    }
  
  
  // choose state
  int s = chooseState(logP);
  state.o(K,O) = C(0,s);
  return state;
}


/////////////////////////////////////////////////////////////////
// scores an object in a category. two parts: crp and likelihood
//
// K: (int) feature category (view) label
// O: (int) object index
double scoreObject(State& state, int K , int O)
{
  // find all the indices in state.f where the element == K
  // features corresponding to this view K
  std::vector<int> theseF;
  int i,j;
  for(i = 0; i < state.f.size2(); i++)
    {
      if(state.f(0,i) == K+1) // DEBUG
	{
	  theseF.push_back(i);
	}
    }

  // crp
  double logP;
  MatrixD M1 = project(state.o, range(K, K+1), range(0, state.o.size2()));
  int sumO = CountInstances(M1, state.o(K,O));
  if(sumO > 1) 
    {
      logP = log( ((double)sumO - 1.0) / ((double)state.O - 1 + state.crpPriorC));  
    }
  else
    {
      logP = log( ( state.crpPriorC / ((double)state.O - 1.0 + state.crpPriorC)));
    }
  
  // score likelihood of data
  M1 = get_row(state.o, K);
  MatrixD theseData = find_indexes(M1, state.o(K,O));
  theseData(0,O) = 0; // eliminate this object
  
      
  for(i=0; i < theseF.size(); i++)
    {
      int f = theseF[i];
      std::vector<double> V;
      for(j=0;j < theseData.size2(); j++)
	{
	  if((int)theseData(0,j) == 1)
	    {
	      V.push_back(state.data(j,f));
	    }
	}
      
      MatrixD M2(1, V.size());
      for(j=0;j<V.size();j++)
	{
	  M2(0,j) = V[j];
	}

      logP = logP + NG_cat(M2, state.data(O,f), state.NG_mu(0,f),
			   state.NG_k(0,f), state.NG_a(0,f), state.NG_b(0,f));
      
    }
  
  return logP;
}

/////////////////////////////////////////////////////////////////
// probability of a datum given priors and other data
//
// data: column data
// newData: real
// this is based on kevin murphy's cheat sheet (NG.pdf)
// data are assumed to be a vector
// mu0, k0, a0, b0 are hyperparameters
// NOTE: this version is for the gibbs sampler for categories
double NG_cat(const MatrixD& data, double newData, double mu0, double k0, double a0, double b0)
{
  // this is updating based on old data
  double len, meanData;
  double logProb;
  
  if(data.size2() == 0)
    {
      // do nothing 
    }
  else
    {
      // NOTE: this could be cached 
      double len = (double)length(data);
      double meanData = sum(data) / len;

      mu0 = ((k0 * mu0) + (len * meanData)) / (k0 + len);
      k0 = k0 + len;
      a0 = a0 + len / 2.0;
      MatrixD diff1 = data;
      Add(diff1, -meanData);
      double diff2 = meanData - mu0;
      
      b0 = b0 + 0.5 * sum(element_prod(diff1,diff1)) + 
	(k0*len*(diff2*diff2)) / (2.0 * (k0 + len));
    }

  // this is always a scaler
  len = 1.0; //(double)length(newData);
  meanData = newData;

  // now update with new data
  // muN = (k0.*mu0 + len.*meanData) ./ (k0+len);
  double kN = k0 + len;
  double aN = a0 + len/2.0;
  
  double newdiff1 = 0;
  double newdiff2 = meanData - mu0;
  double bN = b0 + 0.5 * (newdiff1 * newdiff1) + (k0 * len * (newdiff2 * newdiff2)) / (2.0 * (k0 + len));
  
  logProb = lgamma(aN) - lgamma(a0) + log(b0) * a0 - log(bN) * aN + 
    log((k0/kN)) * 0.5 + log( (2.0 * GP.PI) ) * (-len/2.0);

  return logProb;

}


////////////////////////////////////////////////////////
// return a binary array same size as M with 0 or 1 
//  in element (i,j) indicating M1(i,j) == val 
MatrixD find_indexes(const MatrixD M, int val)
{
	     
  MatrixD M2 = zeros(M.size1(), M.size2());
  int i,j;
  for(i=0; i < M2.size1() ; i++)
    {
      for(j=0; j < M2.size2() ; j++)
	{ 
	  int m = (int)M(i,j);
	  if(m == val)
	    {
	      M2(i,j) = 1; 
	    }
	}
    }
  
  return M2;
}


/////////////////////////////////////////////////////
// return a new 1 x n matrix that is the nth row of M  
MatrixD get_row(const MatrixD M, int i)
{
  return project(M, range(i, i+1) , range(0, M.size2()));
}


// assume column vectors , vals will be treated as
// integers find M1's not in M2 , return sorted 
MatrixD setdiff(const MatrixD& M1, const MatrixD& M2)
{
  int i,j;
  int sz1 = M1.size2();
  int sz2 = M2.size2();

  std::vector<double> temp_v;
  for(i=0; i < sz1; i++)
    {
      // go through all the M2's to see if there is a match
      bool found = false;
      for(j=0; j < sz2; j++)
	{
	  if(M1(0,i) == M2(0,j))
	    {
	      found = true;
	      break;
	    }
	}

      // if there was no match save the M1
      if(!found)
	{
	  temp_v.push_back(M1(0,i));
	}
    }

  // create a matrix to return
  MatrixD M3(1,temp_v.size());
  std::sort(temp_v.begin(), temp_v.end());
  for(i = 0; i < temp_v.size() ; i++)
    {
      M3(0,i) = temp_v[i];
    }

  return M3;
}


double scoreFeature(State& state, double f)
{
  // score feature
  // DGREEN : adjust for c++ indexing
  int K = (int)state.f(0,f) - 1;
  MatrixD M = project(state.o, range(K, K+1) , range(0, state.o.size2()));
  MatrixD c = unique(M);
  double logP = 0;
  int j,k,l;
  int len = c.size2();
       
  for(j=0; j < len ; j++)
    {
      // find indexes where state.o(thisK,:)  == c(0,j)
	  std::vector<int> indexes;
	  for(k=0; k < state.o.size2(); k++)
	    {
	      if(state.o(K,k) == c(0,j))
		indexes.push_back(k);
	    }
	  
	  // save to M
	  int sz = indexes.size();
	  MatrixD M2(sz,1);
	  for(l=0;l < sz; l++)
	    {
	      M2(l,0) = state.data(indexes[l], f);
	    }
	  
	  logP = logP + NG(M2, state.NG_mu(0,f), state.NG_k(0,f), 
				     state.NG_a(0,f), state.NG_b(0,f));
	  	    
	}

  return logP;
}





//////////////////////////////////////////////////////////
// the probability of a partition under the CRP
//
// cats: (integer array) storing assignment of categories where each element
//    stores the category index
// gamma: (real) CRP parameter
double crp(const MatrixD& cats, double gama)
{
  MatrixD u = unique(cats); // unique categories
  int len = length(u);
  MatrixD num = zeros(1,len);
  

  int i;
  for(i=0; i < len ; i++)
    {
      int index = (int)u(0,i);

      int num_sz = length(num);
      // check if we need to resize num
      if(index > num_sz)
	{
	  // copy current num vals into new larger array
	  MatrixD M = zeros(1, index);
	  project(M, range(0,1), range(0, num_sz)) = num;
	  num = M;	
	}
      else if(index < 1)
	{
	  cout<<" crp :  index is zero, skipping " << index;
	}
      else
	{
	  // number of elements in each category
	  // DGREEN : adjust index for c++ indexing
	  num(0, index - 1) = CountInstances(cats, index); // sum(cats==index);
	}
    }

  double logP = prob_of_partition_via_counts(num, gama);

  return logP;
}

//////////////////////////////////////////////////////////////////
// probability of the partition in ns under a CRP with concentration parameter
// gama (note that gama here is NOT the gamma function but just a number)
double prob_of_partition_via_counts(MatrixD& ns, double gama)
{
  //  ns=ns(ns~=0); // only consider classes that are not empty
  ns = StripZeros(ns);
  double k = (double)length(ns); // number of classes
  double n = sum(ns); //number of samples
  double l = sum(gammaln(ns)) + k*log(gama) + lgamma(gama) - lgamma(n+gama); 
  return l;
}


MatrixD gammaln(const MatrixD M)
{
  MatrixD M2(M.size1(), M.size2());

  int i,j;
  int index = 0;

  for(i=0;i<M.size1();i++)
    {
      for(j=0;j<M.size2();j++)
	{
	  M2(i,j) = lgamma(M(i,j));
	}
    }

  return M2;
}


/////////////////////////////////////////////
// return a new matrix that has all zero 
// elements removed
MatrixD StripZeros(const MatrixD& M)
{
  int count = CountInstances(M, 0);
  MatrixD M2(1, M.size2() - count);
  int i,j;
  int index = 0;

  for(i=0;i<M.size1();i++)
    {
      for(j=0;j<M.size2();j++)
	{
	  int val = (int)M(i,j);
	  if(val != 0)
	    {
	      M2(0,index++) = val;
	    }
	}
    }
  return M2;
}


///////////////////////////////////////////////
//  count the number of times val appears in M
int CountInstances(const MatrixD& M, int val)
{
  int count = 0;
  int i,j;
  for(i=0;i<M.size1();i++)
    {
      for(j=0;j<M.size2();j++)
	{
	  int temp = (int)M(i,j);
	  if(temp == val)
	    count++;
	}
    }

  return count;
}



////////////////////////////////////////////
// return unique elements of M in sorted 
// order as a row matrix
MatrixD unique(const MatrixD& M)
{
  int i,j;
  std::map<int, int> vals;
  for(i=0; i < M.size1(); i++)
    {
    for(j=0; j < M.size2(); j++)
      {
	int v = (int)M(i,j);
	vals[v] = v;
      }
    }

  std::map<int,int>::iterator it = vals.begin();
  std::vector<int> temp;
  for(; it != vals.end(); it++)
    {
      temp.push_back(it->second);
    }

  std::sort(temp.begin(), temp.end());
  MatrixD result(1, temp.size());
  for(i=0; i < result.size2() ; i++)
    {
      result(0,i) = temp[i];
    }

  return result;
}



////////////////////////////////////////////////////////////////////
// this samples category partions given # objects from crp prior
//
// n: (integer) total number of objects to be partitioned
// gama: (real) scalar parameter for CRP
//
// partition: (integeger 1xn array) assignment of category for each object
MatrixD sample_partition(int n, double gamma)
{
  using namespace boost::assign;

  MatrixD partition = ones(1, n);
 
    // classes store the number of objects assigned to each category; it always has
  // the total number of categories plus 1. The last element is 0, which indicates
  // the new class with no objects.
  std::vector<int> classes;
  classes += 1,0;

  int i,j;
  for(i=2 ; i <= n; i++)
    {
      std::vector<double> classprobs;

      for(j=0 ; j < classes.size() ; j++)
	{
	  // Calculate probabilities for each existing category and for the new
	  // category to assign to the i-th object.
	  double denom = (double)i - 1.0 + gamma;
	  if( classes[j] > 0.5)
	    {
	      //	      cout << "EXist" << endl;
	      // probability for the existing category j
	      double val = (double)classes[j];
	      classprobs.push_back(val/denom);
	    }
	  else
	    {
	      //cout << "New" << endl;
	      // probability for the new category (classes(j)=0)
	      classprobs.push_back(gamma / denom);
	    }
	}
      
      // cumulative probability function
      MatrixD cumclassprobs = cumsum2(classprobs);
      

      //Take a random draw to determine which category the i-th object should  belong.
      std::vector<int> V;
      int k = 0;
      double rand = GP.Rand.next();
      for(k=0; k < cumclassprobs.size2(); k++)
	{
	  double d = cumclassprobs(0,k);
	  if(rand < d)
	    {
	      V.push_back(k);
	    }
	}

      int c = *std::min_element(V.begin(), V.end());
      // DGREEN : add one for c++ indexing
      partition(0,i-1) = c + 1;
      classes[c] = classes[c] + 1; //  total no. of objects in that category

      //  if we add new category, need to replace placeholder
      if(c == classes.size() - 1)
	{
	  classes.push_back(0);
	}

    }
  
  return partition;
}




///////////////////////////////
// return i from  M(0, :) 
//  where M(0, i) > rand
// ALERT! : assumes M is 1 x n 
// return first element > rand
int GetFirstIndex(const MatrixD& M, double val)
{  
  double rand = GP.Rand.next();
  int n = M.size2();
  
  int i;
  int result = 0;
  for(i=0;i < n; i++)
    {    
      if(M(0,i) > rand)
	{
	  result = i;
	  break;
	} 
    }
  
  return result;
}



/////////////////////////////////////////////////
// VERIFIED
void SetaRange(State& state)
{
  double temp_d = (double)state.O/2.0;
  double binsD = (double)GP.bins;

  MatrixD tmp = linspace(0.5, temp_d / (temp_d + 1.0) , (binsD+1.0) / 2.0);
  matrix_range< MatrixD> mr3(state.paramRange, range(0, 1), range(0 , (GP.bins-1) / 2));
  
  MatrixD y = -tmp + ones(1, tmp.size2());
  y = element_div(tmp, y);
  
  state.aRange = Concat(mr3, y);  

}


////////////////////////////////////////////////////
// VERIFIED
void SetCrpParameterRanges(State& state)
{
  double F = (double)state.F;
  double binsD = (double)GP.bins;
  MatrixD tmp = linspace(0.5, F / (F + 1.0), (binsD+1.0) / 2.0);

  matrix_range< MatrixD> mr1(state.paramRange, range(0, 1), range(0 , (GP.bins-1) / 2));

  MatrixD y =  ones(1, tmp.size2()) - tmp;
  
  y = element_div(tmp, y);
  
  state.crpKRange = Concat(mr1, y);
  
  double O = (double)state.O;
  tmp = linspace(0.5, O / (O + 1.0), (binsD+1.0) / 2.0);
  matrix_range< MatrixD> mr2(state.paramRange, range(0, 1), range(0 , (GP.bins-1) / 2));
  
  y = -tmp + ones(1, tmp.size2());
  y = element_div(tmp, y);
  
  state.crpCRange = Concat(mr2, y);


}

/////////////////////////////////////////////
// VERIFIED
void SetMuBetaRanges(State& state)
{
  int f = 0;
  state.muRange.resize(state.F, 30);
  state.bRange.resize(state.F, GP.bins);

  for(f=0;f < state.F; f++)
    {
      // mu
      MatrixD M1 = project(state.data, range(0, state.data.size1()), range(f,f+1));
      double t1 = *std::min_element(M1.begin1(), M1.end1());
      double t2 = *std::max_element(M1.begin1(), M1.end1());
      MatrixD M2  = linspace(t1,t2,30);
      project(state.muRange, range(f, f+1), range(0, M2.size2())) = M2;
      // set b max based on empirical SSD
      M2 = M1 - (ones(M1.size1(),M1.size2()) * mean(M1));
      M2 = element_prod(M2,M2);
      double ssd = sum(M2);      
 
      M1 = linspace(0.5, ssd / (ssd + 1), (GP.bins + 1) / 2);      
      M2 = ones(1, M1.size2()) - M1;
      M2 = element_div(M1, M2);
      matrix_range< MatrixD> mr1(state.paramRange, range(0, 1), range(0 , (GP.bins-1) / 2));

      M2 = Concat(mr1, M2);  
      project(state.bRange, range(f, f+1), range(0, M2.size2())) = M2;

    }

}

double mean(const MatrixD& M)
{
  int m = M.size1();
  int n = M.size2();
  int i,j;
  double mean = sum(M);
  mean = mean / ((double)m*n);
  return mean;
}



void SaveMatrix(const MatrixD& M, std::string filename)
{
  ofstream out(filename.c_str()); 
  if(!out) 
    { 
      cout << "Cannot open file.\n"; 
      return; 
    } 

  int m = M.size1();
  int n = M.size2();

  cout.setf(std::ios::scientific, std::ios::floatfield);
  cout.precision(10);

  int i,j;
  for(i=0;i < m; i++)
    {
      for(j=0;j<n;j++)
	{
	  out<<M(i,j);
	  if(j<(n-1))
	    out << ",";	 
	}
      out<<endl;
    }

    
  out.close(); 
}


// concat the two matrices , returns empty matrix
// if there is no common dimension
MatrixD Concat(const MatrixD& M1, const MatrixD& M2)
{
  MatrixD R;

  int m1 = M1.size1();
  int n1 = M1.size2();
  int m2 = M2.size1();
  int n2 = M2.size2();

  int i,j;

  if(m1 == m2)
    {
      R.resize(m1, n1 + n2);
      for(i=0;i<m1;i++)
	{
	  for(j=0;j<(n1+n2);j++)
	    {
	      if(j<n1)
		{
		  R(i,j) = M1(i,j);
		}
	      else
		{
		  R(i,j) = M2(i,j-n1);
		}
	    }
	}

    }
  else if(n1 == n2)
    {
      R.resize(m1 + m2, n1);
      for(i=0;i<n1;i++)
	{
	  for(j=0;j<(m1+m2);j++)
	    {
	      if(j<m1)
		{
		  R(j,i) = M1(j,i);
		}
	      else
		{
		  R(j,i) = M2(j-m1,i);
		}
	    }
	}
    }

  return R;

}


// assume 2D matrix, add val to every element
void Add(MatrixD& M , double val)
{
  int m = M.size1();
  int n = M.size2();
  int i,j;
  for(i=0;i<m;i++)
    {
      for(j=0;j<n;j++)
	{
	  M(i,j) += val;
	}
    }
}




void Print(const MatrixD& M, const std::string msg)
{
  cout << msg << " = " << endl << M << endl << endl;
}

void PrintV(const std::vector<double>& V, const std::string msg)
{
  int i;
  
  cout << msg << " = " << endl;
  for(i=0;i < V.size(); i++)
    {
      cout << V[i] ;
      if(i < (V.size() - 1))
	{
	  cout << ",";
	}
    }

  cout << endl;

}


// compute cummulative sum , expects
//  a 1 x n or n x 1 matrix and sums
//  along the n dimension. add support
//  for m x n matrices later if needed.
MatrixD cumsum(const MatrixD& M, int dim )
{
  MatrixD result(M.size1(), M.size2());
  if(M.size1() == 1)
    {
      int i = 0;
      result(0,0) = M(0,0);
      for(i = 1; i < M.size2(); i ++)
	{
	    result(0,i) = result(0, i-1) + M(0,i);
	}
    }
  else if(M.size2() == 1)
    {
      int i = 0;
      result(0,0) = M(0,0);
      for(i = 1; i < M.size2(); i ++)
	{
	  result(i,0) = result(i-1,0) + M(i,0);
	}
   
    }

  return result;
}

MatrixD cumsum2(const std::vector<double>& V)
{
  MatrixD result(1, V.size());
  
  int i = 0;
  result(0,0) = V[0];
  for(i = 1; i < V.size(); i ++)
    {
      result(0,i) = result(0, i-1) + V[i];
    }
  
  return result;
}

void printMatrixD(MatrixD mat, int rows, int cols, int dec) {
    std::cout << std::fixed << std::setprecision(dec);
    for(int r = 0; r < rows; r++) {
      for(int c = 0; c < cols; c++) {
	std::cout << mat(r, c) << '\t';
      }
      std::cout << '\n';
    }
}

// returns the sum of all the elements
double sum(const MatrixD& M)
{
  double result = 0;
  int m = M.size1();
  int n = M.size2();
  int i,j;

  for(i=0;i<m;i++)
    {
      for(j=0;j<n;j++)
	{
	  result += M(i,j);
	}
    }
  
  return result;
}

////////////////////////////////////////////
// init a matrix monotonically increasing 
// steps of 1 from [start , end ] (inclusive)
MatrixD init_matrix_mti(int start, int end)
{
  int len = end - start + 1;
  MatrixD M(1, len);
  int i;
  for(i=0; i < len ; i++)
    {
      M(0,i) = start + i;
    }
  
  return M;
}


// returns matrix initialized with ones 
MatrixD ones(int nrows, int ncols)
{
  return init_matrix(nrows, ncols, 1.0);
}


// returns matrix initialized with ones 
MatrixD zeros(int nrows, int ncols)
{
  return init_matrix(nrows, ncols, 0);
}

MatrixD init_matrix(int nrows, int ncols, double val)
{
  MatrixD M(nrows, ncols);
  
  int i,j;

  for(i=0;i<M.size1();i++)
    {
        for(j=0;j<M.size2();j++)
	  {
	    M(i,j) = val;
	  }
    }

  return M;
}


int length(const MatrixD& M)
{
  int l;

  if(M.size1() > M.size2())
    l = M.size1();
  else
    l = M.size2();

  return l;
}


///////////////////////////////////////////////////////
// VERIFIED
MatrixD linspace(double x1, double x2, int num_elements)
{
  MatrixD  M(1,num_elements);

  double x3 = (double)(num_elements - 1);
  
  double step = (x2 - x1) / x3;
  
  M(0,0) = x1;
  int i = 0;
  for(i = 1; i < M.size2(); i++)
    {
      M(0,i) = x1 + ((double)i*step);
    }

  return M;
}


//////////////////////////////////////////////////////////////
// load a cfg file and set GlobalParams based on contents
void LoadCfg(std::string file, GlobalParameters& GP)
{
   
  ifstream in(file.c_str());
  
  if (!in.is_open())
    return;
  
  typedef tokenizer< char_separator<char> > Tokenizer;
  char_separator<char> sep(",");
}


/////////////////////////////////////////////////////////////////////
// expect a csv file of data
void LoadData(std::string file, boost::numeric::ublas::matrix<double>& M)
{
   
  ifstream in(file.c_str());
  
  if (!in.is_open())
    return;
  
  typedef tokenizer< char_separator<char> > Tokenizer;
  char_separator<char> sep(",");

  string line;
  int nrows = 0; 
  int ncols = 0;
  std::vector<string> vec;

  // get the size first
  while (std::getline(in,line))
    {
      Tokenizer tok(line, sep);
      vec.assign(tok.begin(), tok.end());
      ncols = vec.end() - vec.begin();
      nrows++;
    }

  cout << "num rows = "<< nrows << "  num cols = " << ncols << endl;


  // create a matrix to hold data
  matrix<double> Data(nrows, ncols);
  
  // make second pass 
  in.clear();
  in.seekg(0);
 

  int r = 0;
  while (std::getline(in,line))
    {
      Tokenizer tok(line, sep);
      vec.assign(tok.begin(), tok.end());
      int i = 0;
      for(i=0; i < vec.size() ; i++)
	{ 
	  Data(r, i) = ::strtod(vec[i].c_str(), 0);
	}

      r++;
    }
 
  M = Data;

}

double get_element(MatrixD M, int i, int j)
{
  return M(i,j);
}
