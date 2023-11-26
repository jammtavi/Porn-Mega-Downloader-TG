FROM python:3.10
WORKDIR /app
COPY . /app/
RUN pip install -r requirements.txt
RUN apt -qq update && apt -qq install -y git wget pv jq python3-dev ffmpeg mediainfo
RUN apt-get install neofetch wget -y -f
CMD ["python", "bot.py"]
