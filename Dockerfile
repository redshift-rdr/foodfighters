FROM balenalib/raspberry-pi-alpine-python:latest
WORKDIR /rynance
ADD . /rynance
RUN pip install -r requirements.txt
CMD ["python","rynance.py"]
EXPOSE 5000
