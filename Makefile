
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

convert : Cluster.cpp Cluster.h Suffstats.cpp Suffstats.h utils.h utils.cpp numerics.h numerics.cpp View.h View.cpp test_view.cpp
	$(CXX) -o runModel Cluster.cpp Suffstats.cpp utils.cpp test_view.cpp numerics.cpp View.cpp $(CXXOPTS)
