fix-imports:
	autoflake --in-place --recursive --remove-unused-variables --remove-all-unused-imports .
	isort -rc .
	black .

docker-build:
	docker image build -t covid19-br .

docker-collect:
	docker container run --rm --name covid19-br --volume $(PWD)/data/output:/opt/covid19-br/data/output covid19-br ./collect.sh

docker-run:
	docker container run --rm --name covid19-br --volume $(PWD)/data/output:/opt/covid19-br/data/output covid19-br ./run.sh

docker-deploy:
	docker container run --env-file ./.env --rm --name covid19-br --volume $(PWD)/data/output:/opt/covid19-br/data/output covid19-br ./deploy.sh