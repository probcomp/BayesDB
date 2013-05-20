OPTIMIZED = 
ifdef OPTIMIZED
CXXOPTS := -O2 -g $(CXXOPTS)
else
CXXOPTS := -g $(CXXOPTS) 
endif

CC = gcc
CXX = g++
CXXOPTS :=  $(CXXOPTS) -lm -lboost_program_options -L$(BOOST_ROOT)/lib -I$(BOOST_ROOT)/include

INC=include/CrossCat
SRC=src
OBJ=obj
# Assume BOOST_ROOT set as environment variable.
# /usr/local/boost
BIN = main
MAIN = main.cpp
NAMES = ContinuousComponentModel MultinomialComponentModel ComponentModel \
	Cluster View State \
	utils numerics RandomNumberGenerator DateTime
HEADERS = $(foreach name, $(NAMES), $(INC)/$(name).h)
SOURCES = $(foreach name, $(NAMES), $(SRC)/$(name).cpp)
OBJECTS = $(foreach name, $(NAMES), $(OBJ)/$(name).o)

all: obj # bin

clean:
	rm -f $(BIN) $(OBJECTS) core *.stackdump *.gch $(TESTS)

bin: $(OBJECTS) $(BIN) $(MAIN) $(HEADERS)

obj: $(OBJECTS)

$(OBJ)/%.o: $(SRC)/%.cpp $(HEADERS)
	$(CXX) -c $< -o $@ $(CXXOPTS) -I$(INC)

$(BIN): $(OBJECTS) $(MAIN) $(HEADERS)
	$(CXX) -o $(BIN) $(MAIN) $(OBJECTS) $(HEADERS) $(CXXOPTS) -I$(INC)
