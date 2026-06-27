version: "3.9"

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: agricrop-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - MONGODB_URI=mongodb://mongo:27017
      - MONGODB_DB_NAME=agricrop
    depends_on:
      - mongo
    volumes:
      - ./logs:/app/logs
      - ./tmp:/app/tmp
      - ./ai_models:/app/ai_models
      - ./datasets:/app/datasets
    restart: unless-stopped

  mongo:
    image: mongo:7.0
    container_name: agricrop-mongo
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    restart: unless-stopped

volumes:
  mongo_data:
