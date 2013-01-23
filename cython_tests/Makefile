
all:
	python setup.py build_ext --inplace

clean:
	rm -rf build continuous_component_model_test.so

run: all
	python use_ccm.py
