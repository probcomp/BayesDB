NAMES = ContinuousComponentModel MultinomialComponentModel State
SOS = $(foreach name, $(NAMES), $(name).so)
PYXS = $(foreach name, $(NAMES), $(name).pyx)
INTERMEDIATE = $(foreach name, $(NAMES), $(name).cpp)
RUN = state_test.py

all: sos

sos: $(SOS)

$(SOS): $(PYXS)
	python setup.py build_ext --inplace

clean:
	rm -rf build $(SOS) $(INTERMEDIATE)

run: all
	python $(RUN)
