# Taken from https://gist.github.com/mpneuried/0594963ad38e68917ef189b4e6a269db
APP_NAME=suas-vision
PORT=8003

build: ## Build the container
	docker build -t $(APP_NAME) .

run:
	docker run -p=$(PORT):$(PORT) --env-file env.txt \
		--name="$(APP_NAME)" $(APP_NAME)

kill:
	./kill.sh $(APP_NAME)
