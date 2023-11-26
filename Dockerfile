FROM python:3.10

WORKDIR /app
COPY . /app/

# Install required dependencies, upgrade pip, and install ffmpeg
RUN apt-get update && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

CMD ["python", "bot.py"]
