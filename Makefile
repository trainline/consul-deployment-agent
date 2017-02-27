init:
	pip install -r requirements.txt

init-lint:
	pip install -r lint-requirements.txt

init-test:
	pip install -r test-requirements.txt

lint:
	pyflakes .

test:
	nosetests --verbosity=2 tests

test-windows-deployment:
	nosetests --verbosity=2 tests/test_deployment_windows.py

test-linux-deployment:
	nosetests --verbosity=2 tests/test_deployment_linux.py
