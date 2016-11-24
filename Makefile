unit:
	py.test -v

coverage:
	py.test --cov=websmash --cov-report=html --cov-report=term-missing
