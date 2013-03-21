NAMES = ContinuousComponentModel MultinomialComponentModel State
SOS = $(foreach name, $(NAMES), $(name).so)
INTERMEDIATE = $(foreach name, $(NAMES), $(name).cpp)
RUN = state_test.py

all:
	python setup.py build_ext --inplace

clean:
	rm -rf build $(SOS) $(INTERMEDIATE)

run: all
	python $(RUN)
