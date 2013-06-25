CPP_DIR=cpp_code
CYT=tabular_predDB/cython_code
DOC=docs
TEST=tabular_predDB/tests
XNET=tabular_predDB/binary_creation


all: cython doc

clean:
	cd $(CPP_DIR) && make clean
	cd $(CYT) && make clean
	cd $(DOC) && make clean
	cd $(TEST) && make clean
	cd $(XNET) && make clean

cpp:
	cd $(CPP_DIR) && make

cython:
	cd $(CYT) && make

doc:
	cd $(DOC) && make

runtests:
	cd $(TEST) && make runtests

tests:
	cd $(TEST) && make tests

xnet:
	cd $(XNET) && make
