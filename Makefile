# Taken from https://gist.github.com/mpneuried/0594963ad38e68917ef189b4e6a269db
APP_NAME=suas-vision
PORT=8003

update:
	wget -O ./vision/odlc/models/alphanumeric_model.pth \
		https://uas.seas.ucla.edu/model/alphanumeric_model.pth && \
	wget -O ./vision/odlc/models/emergent_model.pth \
		https://uas.seas.ucla.edu/model/emergent_model.pth

build:
	docker compose build

run:
	docker compose up -d

restart:
	docker compose up -d --build

kill:
	docker compose kill

test:
	docker compose build && docker compose up -d && \
		docker exec suas-onboard-vision-web-1 python3 -m unittest
