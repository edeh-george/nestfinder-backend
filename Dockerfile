# Base layer to build image
FROM python:3.9

# Set the working directory for the following steps
WORKDIR /home/app

# Copy application file
COPY . .

# Create Virtual environment and install dependencies
RUN python3 -m venv venv && \
    venv/bin/pip3 install --no-cache-dir -r requirements.txt


# Move to the backend directory
WORKDIR ./backend

#Run database migrations and collect static files
RUN ../venv/bin/python3 manage.py makemigrations && \
    ../venv/bin/python3 manage.py migrate && \
    ../venv/bin/python3 manage.py collectstatic  --noinput

EXPOSE 8443

CMD ["home/app/venv/bin/daphne", "-e", "ssl:8443:privateKey=localhost+1-key.pem:certKey=localhost+1.pem", "nestfinder.asgi:application"]
