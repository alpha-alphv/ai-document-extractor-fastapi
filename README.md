# ai-document-extractor-fastapi
This project is a FastAPI application designed to extract information from documents, containerized with Docker.

## Run with Docker
1. **Clone the Respository**
```
git clone https://github.com/yourusername/ai-document-extractor-fastapi.git
cd ai-document-extractor-fastapi
```

2. **Create a virtual environment and activate it:**
```
python -m venv venv
source venv/bin/activate
```

3. **Build and Run the Docker Container. Ensure Docker is installed and running. Use the following command to build and start the application:**
```
docker-compose up --build
```

4. **Access the ApplicationOnce the container is running, open your browser or use a tool like curl to access the FastAPI app via SwaggerUI at:**
```
http://localhost:8000/docs
```
