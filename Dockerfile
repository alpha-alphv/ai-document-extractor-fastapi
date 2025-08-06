# Use a lightweight Python base image
FROM python:3.11-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./app /app


# Command to run the FastAPI application using Uvicorn
CMD ["bash", "-lc", "\
    echo '=> Starting FastAPI'; \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
  "]