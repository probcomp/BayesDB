
OPTIMIZED = 

CC = gcc
CXX = g++
CXXOPTS :=  -lm -lboost_program_options

MAIN = test_view.cpp
SRC = Cluster.cpp Suffstats.cpp utils.cpp numerics.cpp View.cpp $(MAIN)
OBJ = $(SRC:.cpp=.o)
H = $(SRC:.cpp=.h)
BIN = runModel

ifdef OPTIMIZED
CXXOPTS := -O2 -g $(CXXOPTS)
else
CXXOPTS := -g $(CXXOPTS)	
endif

all: $(BIN)

$(BIN): $(OBJ)
	$(CXX) -o $(BIN) $(OBJ) $(CXXOPTS)
