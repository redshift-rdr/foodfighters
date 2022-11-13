FROM balenalib/raspberry-pi-alpine-python:latest
WORKDIR /foodfighters
ADD . /foodfighters
RUN pip install -r requirements.txt
CMD ["python","foodfighters.py"]
EXPOSE 5000
