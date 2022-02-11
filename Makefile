unit:
	py.test -v

coverage:
	py.test --cov=websmash --cov-report=html --cov-report=term-missing

corelint:
	flake8 websmash --count --select=E9,F63,F7,F82 --show-source --statistics

lint:
	flake8 websmash --count --exit-zero --max-complexity=20 --statistics
