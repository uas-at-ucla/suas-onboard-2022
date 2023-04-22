# Taken from https://gist.github.com/mpneuried/0594963ad38e68917ef189b4e6a269db
APP_NAME=suas-vision
PORT=8003

tidy:
	rm -rf ./vision/images/debug/*.png
	
build:
	wget -O ./vision/odlc/models/alphanumeric_model.pth \
		https://uas.seas.ucla.edu/model/alphanumeric_model.pth && \
	wget -O ./vision/odlc/models/emergent_model.pth \
		https://uas.seas.ucla.edu/model/emergent_model.pth && \
	wget -O ./vision/odlc/models/mobilenet_large.pth \
		http://uas.seas.ucla.edu/model/mobilent_text.pth && \
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

coverage:
	docker compose build && docker compose up -d && \
		docker exec suas-onboard-vision-web-1 bash -c \
		"coverage run -m unittest; coverage html -i"
	
