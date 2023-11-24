FROM python:3.10
WORKDIR /app
COPY . /app/
RUN apt -qq update && apt -qq install -y git wget pv jq python3-dev ffmpeg mediainfo
RUN apt-get install neofetch wget -y -f
RUN pip install -r requirements.txt
CMD ["python", "bot.py"]
