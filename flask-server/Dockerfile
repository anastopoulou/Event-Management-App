FROM python:3.12
WORKDIR /app
COPY . .
RUN apt update -y
RUN apt upgrade -y
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-u", "main.py"]