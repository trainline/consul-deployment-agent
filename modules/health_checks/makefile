init:
	pip install -r requirements.txt

init-test:
	pip install -r test-requirements.txt

test: init init-test
	nosetests --verbosity=2 tests