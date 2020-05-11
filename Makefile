.PHONY := integration-test, test-image

test-image:
	docker build --tag cda:dev --file Dockerfile .
	# docker images --quiet cda:dev > test-image

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

integration-test: test-image
	docker run --rm --entrypoint bash cda:dev -c 'nosetests tests/* integration-tests/*'
