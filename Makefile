
OPTIMIZED = 

CC = gcc
CXX = g++

CXXOPTS :=  -lm -lboost_program_options

ifdef OPTIMIZED
CXXOPTS := -O2 -g $(CXXOPTS)
else
CXXOPTS := -g $(CXXOPTS)	
endif

all:   convert

convert : cluster.cpp cluster.h suffstats.cpp suffstats.h utils.h utils.cpp numerics.h numerics.cpp view.h view.cpp test_view.cpp
	$(CXX) -o runModel cluster.cpp suffstats.cpp utils.cpp test_view.cpp numerics.cpp view.cpp $(CXXOPTS)
