FROM python:3.9-slim
RUN apt-get update
RUN apt install build-essential -y
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install tesseract-ocr -y
RUN apt-get install wget -y
RUN apt-get install git -y
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
RUN python -m pip install detectron2 -f \
  https://dl.fbaipublicfiles.com/detectron2/wheels/cpu/torch1.10/index.html

# RUN python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
COPY . /app
RUN ["wget", "-O", "/app/odlc/models/alphanumeric_model.pth", \
     "https://uas.seas.ucla.edu/model/alphanumeric_model.pth"]
RUN chmod +rwx /app/odlc/models/alphanumeric_model.pth
RUN ["wget", "-O", "/app/odlc/models/emergent_model.pth", \
     "https://uas.seas.ucla.edu/model/emergent_model.pth"]
RUN chmod +rwx /app/odlc/models/emergent_model.pth
WORKDIR /app
ENTRYPOINT ["./start_gunicorn.sh"]