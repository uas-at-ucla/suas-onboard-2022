FROM python:3.9-slim
RUN apt-get update
RUN apt install build-essential -y
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install tesseract-ocr -y
RUN apt-get install wget -y
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
RUN python -m pip install detectron2 -f \
  https://dl.fbaipublicfiles.com/detectron2/wheels/cpu/torch1.10/index.html
COPY . /app
WORKDIR /app
ENTRYPOINT ["./start_gunicorn.sh"]
