BIN = build/exe.linux-x86_64-2.7/hadoop_line_processor 

all: bin

bin: $(BIN)

$(BIN):
	python setup.py build

clean:
	rm -rf build build.err build.out
