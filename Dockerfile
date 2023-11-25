FROM python:3.10

WORKDIR /app
COPY . /app/

# Install required dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    pip install -r requirements.txt

CMD ["python", "bot.py"]
