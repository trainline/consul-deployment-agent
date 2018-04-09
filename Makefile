init:
	pip install -r requirements.txt

init-lint:
	pip install -r lint-requirements.txt

init-test:
	pip install -r test-requirements.txt

lint: init init-lint
	pyflakes .

test: init init-test
	nosetests --verbosity=2 tests/*

test-windows-deployment: init init-test
	nosetests --verbosity=2 tests/test_deployment_windows.py

test-linux-deployment: init init-test
	nosetests --verbosity=2 tests/test_deployment_linux.py
