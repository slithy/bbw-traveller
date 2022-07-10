all: build

build:
	docker-compose up --build

test:
	#env PYTHONPATH=. python3.7 tests/monster_test.py
	#env PYTHONPATH=. python3.7 tests/character_test.py
	env PYTHONPATH=. python3.7 tests/equipment_test.py

clean:
	docker rm -v `docker ps --filter status=exited -q 2>/dev/null` 2>/dev/null
	docker rmi `docker images --filter dangling=true -q 2>/dev/null` 2>/dev/null

clobber:
	@./clean_saves ./save

start:
	sudo systemctl start docker

stop:
	sudo systemctl stop docker

.PHONY: test
