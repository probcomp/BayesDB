
OPTIMIZED = 

CC = gcc
CXX = g++
CXXOPTS :=  -lm -lboost_program_options

MAIN = test_view.cpp
H = Cluster.h Suffstats.h utils.h numerics.h View.h
SRC = Cluster.cpp Suffstats.cpp utils.cpp numerics.cpp View.cpp \
	 RandomNumberGenerator.h $(MAIN)
OBJ = $(SRC:.cpp=.o)
BIN = runModel

ifdef OPTIMIZED
CXXOPTS := -O2 -g $(CXXOPTS)
else
CXXOPTS := -g $(CXXOPTS)	
endif

all: $(BIN)

$(BIN): $(OBJ)
	$(CXX) -o $(BIN) $(OBJ) $(CXXOPTS)

clean:
	rm -f $(BIN) *.o core *.stackdump *.bak *.gch
