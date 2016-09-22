# Copyright (c) Trainline Limited. All rights reserved. See LICENSE.txt in the project root for license information.

init:
	pip install -r requirements.txt

init-test:
	pip install -r test-requirements.txt

test:
	nosetests --verbosity=2 tests
