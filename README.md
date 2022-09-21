# suas-vision
This repo is the vision subsystem of the UAS @ UCLA 2023 SUAS competition.

## Getting Started
First, ensure you have Docker installed. See the instructions
[here](https://docs.docker.com/get-docker/) for your setup.

Then, clone this repo locally:

```
git clone https://github.com/uas-at-ucla/suas-vision
cd suas-vision
```

Build and run the Docker image:
```
make run
```
The server will now be serving requests at localhost:8003. To test your
installation, go to [localhost:8003](http://localhost:8003) in your browser.

## Dummy Server
For development purposes, we have provided a dummy server that will serve
valid (but arbitrary) responses to each of the required APIs. To enable the
dummy server, add an environment variable to the web container that reads:
```
DUMMY=1
```

Note that the dummy server will not validate requests.