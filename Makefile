OPTIMIZED = 
ifdef OPTIMIZED
CXXOPTS := -O2 -g $(CXXOPTS)
else
CXXOPTS := -g $(CXXOPTS)	
endif

CC = gcc
CXX = g++
CXXOPTS :=  $(CXXOPTS) -lm -lboost_program_options

INC=include/CrossCat
SRC=src
OBJ=obj
TEST=tests
CYT=cython
#
BIN = model
MAIN = main.cpp
NAMES = ContinuousComponentModel MultinomialComponentModel ComponentModel \
	Cluster View State \
	utils numerics RandomNumberGenerator DateTime
TEST_NAMES = test_continuous_component_model test_multinomial_component_model \
	test_cluster test_view test_view_speed test_state
CYTHON_NAMES = Makefile setup.py State.pyx
HEADERS = $(foreach name, $(NAMES), $(INC)/$(name).h)
SOURCES = $(foreach name, $(NAMES) $(MAIN), $(SRC)/$(name).cpp)
OBJECTS = $(foreach name, $(NAMES), $(OBJ)/$(name).o)
TESTS = $(foreach test, $(TEST_NAMES), $(TEST)/$(test))
CYTHON = $(foreach name, $(CYTHON_NAMES), $(CYT)/$(name))

all: cython

cython: $(CYT)/State.so

bin: $(OBJECTS) $(BIN)
	./$(BIN)

obj: $(OBJECTS)

# run each test
tests: $(TESTS)
	@echo tests are: $(TESTS) $(foreach test, $(TESTS), && ./$(test))

clean:
	rm -f $(BIN) $(OBJECTS) core *.stackdump *.gch $(TESTS)
	cd $(CYT) && make clean

$(CYT)/State.so: $(HEADERS) $(SOURCE) $(CYTHON)
	cd $(CYT) && make

$(OBJ)/%.o: $(SRC)/%.cpp $(INC)/%.h $(HEADERS)
	$(CXX) -c $< -o $@ $(CXXOPTS) -I$(INC)

$(BIN): $(MAIN) $(OBJECTS)
	$(CXX) -o $(BIN) $(MAIN) $(OBJECTS) $(CXXOPTS) -I$(INC)

$(TEST)/%: $(TEST)/%.cpp $(HEADERS) $(OBJECTS)
	$(CXX) $< -o $@ $(CXXOPTS) -I$(INC) $(OBJECTS)
