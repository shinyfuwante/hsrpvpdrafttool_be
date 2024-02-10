# Use an official Python runtime as a parent image
FROM python:3.11.8-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code/
# Install dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /code/

CMD ["daphne", "backend.asgi:application", "-p", "8000", "-b", "0.0.0.0"]