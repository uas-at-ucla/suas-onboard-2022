FROM python:3.9-slim
RUN apt-get update
RUN apt install build-essential -y
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install wget -y
# RUN apt-get install git -y
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
RUN python -m pip install detectron2 -f \
  https://dl.fbaipublicfiles.com/detectron2/wheels/cpu/torch1.10/index.html

# RUN python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
COPY . /app
WORKDIR /app
ENTRYPOINT ["./start_gunicorn.sh"]
