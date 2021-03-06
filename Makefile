lint:
	autoflake --in-place --recursive --remove-unused-variables --remove-all-unused-imports .
	isort -rc .
	black -l 120 .

docker-build:
	docker image build -t covid19-br .

docker-run-spiders:
	docker container run --rm --name covid19-br --volume $(PWD)/data/output:/app/data/output covid19-br ./run-spiders.sh

docker-run: docker-build
	docker container run --rm --name covid19-br --volume $(PWD)/data/output:/app/data/output covid19-br ./run.sh
	docker container run --rm --name covid19-br --volume $(PWD)/data/output:/app/data/output covid19-br ./run-obitos.sh

docker-build-dev:
	docker image build -t covid19-br-dev --build-arg PYTHON_REQUIREMENTS=requirements-development.txt .

docker-test: docker-build-dev
	docker container run -e PYTHONPATH=. --rm covid19-br-dev pytest tests/

docker-flake8: docker-build-dev
	docker container run --rm covid19-br-dev flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	docker container run --rm covid19-br-dev flake8 . --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics

docker-deploy:
	docker container run --env-file ./.env --rm --name covid19-br --volume $(PWD)/data/output:/app/data/output covid19-br ./deploy.sh

docker-validate: docker-build
	docker container run --rm --name covid19-br --volume $(PWD)/data/output:/app/data/output covid19-br ./validate.sh
