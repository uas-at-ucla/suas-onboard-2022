# Taken from https://gist.github.com/mpneuried/0594963ad38e68917ef189b4e6a269db
APP_NAME=suas-vision
PORT=8003

build:
	docker compose build

run:
	docker compose up -d

restart:
	docker compose restart

kill:
	docker compose kill

test:
	docker compose build && docker compose up -d && \
		docker exec suas-vision-web-1 python3 -m unittest