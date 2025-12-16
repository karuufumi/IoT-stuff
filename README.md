# IoT Backend API

Backend service for an IoT monitoring system built with FastAPI, MongoDB, JWT authentication, and WebSocket-based realtime streaming.

## Features

- User registration and login with JWT authentication
- Protected API endpoints
- Time-series sensor history stored in MongoDB
- Realtime sensor updates via WebSocket
- Clean layered architecture (Controller, Service, Repository)

## Tech Stack

- Python 3.13
- FastAPI
- MongoDB (Async PyMongo)
- JWT (PyJWT)
- WebSockets
- Passlib (bcrypt)
