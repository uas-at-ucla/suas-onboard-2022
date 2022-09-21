# Taken from https://gist.github.com/mpneuried/0594963ad38e68917ef189b4e6a269db
APP_NAME=suas-vision
PORT=8003

run:
	docker compose up -d

restart:
	docker compose restart

kill:
	docker compose kill
