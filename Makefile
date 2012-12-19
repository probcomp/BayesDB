
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

convert : runModel_v2.cpp DateTime.cpp DateTime.h
	$(CXX) -o runModel  runModel_v2.cpp DateTime.cpp  $(CXXOPTS)
