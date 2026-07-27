# Production Deployment & Docker Guide

This document explains what Docker is in simple terms, and how we are using it to deploy the Enterprise Data Copilot application.

## 1. What is Docker?

In traditional software deployment, you might install Python, Node.js, and Postgres directly onto your computer or server. However, this often leads to the infamous **"It works on my machine!"** problem. If your server has a slightly different version of Python, or is missing a specific environment variable, the application might crash.

**Docker solves this by packaging the application and its environment together into a "Container".** 

A container is a lightweight, isolated environment that contains everything your application needs to run: the code, a specific version of a programming language (like Python 3.12), and all necessary dependencies. Because the container contains its own environment, it will run exactly the same way on a Mac, a Windows PC, or an AWS Linux server.

## 2. Docker Concepts

- **Dockerfile**: Think of this as a recipe. It's a text file with instructions on how to build the container environment. We have two Dockerfiles:
  - `backend/Dockerfile`: Tells Docker to get a slim version of Python 3.12, install our `requirements.txt`, copy our backend code, and run the FastAPI server.
  - `frontend/Dockerfile`: Tells Docker to get Node.js, build our React app into static files, and then load those files into **Nginx** (a highly efficient web server) to serve them to users.
- **Image**: Once Docker executes the recipe (the Dockerfile), the result is an Image. An Image is the immutable, built package of your application.
- **Container**: A container is a running instance of an Image. You can run multiple containers from the same image.
- **Docker Compose**: When an application has multiple parts (a frontend, a backend, and a database), running each container manually gets complicated. `docker-compose.yml` is a configuration file that tells Docker how to start **all** these services together, how they should connect to each other on a virtual network, and what ports they should open to the outside world.

## 3. How Our Architecture Works in Production

When we run our application via Docker Compose:

1. **Postgres Container**: A database container spins up securely. It is isolated on a private virtual network (`copilot_net`).
2. **Backend Container**: The FastAPI Python backend spins up. Because it's on the same `copilot_net` network, it can securely talk to the Postgres container using the internal hostname `postgres`. It exposes port `8000`.
3. **Frontend Container (Nginx)**: The compiled React app is served by Nginx. Nginx listens on port `80` (the standard web port). 

### The Nginx Proxy Magic
If a user goes to `http://localhost/`, Nginx serves them the React application. 
However, what happens when the React app needs to fetch data from the backend? Instead of trying to connect directly to the backend from the user's browser, the React app sends the request back to Nginx at `http://localhost/api/`. Nginx intercepts any request starting with `/api/` and silently forwards (proxies) it to the Backend container (`http://backend:8000/`) over the private Docker network. 

This proxy approach prevents CORS (Cross-Origin Resource Sharing) security errors in the browser and keeps our backend completely hidden from the public internet if we choose not to expose port 8000 externally.

## 4. How to Deploy

To deploy the application in production (or test the production build locally), follow these steps:

1. **Stop Dev Servers**: Ensure you have stopped any local running dev servers (like `npm run dev` or `uvicorn`) so they don't block the ports.
2. **Environment Setup**: Ensure you have a `.env` file in the root directory containing your required keys (e.g., `GROQ_API_KEY`).
3. **Build and Run**: Run the following command in the terminal at the root of the project:
   ```bash
   docker-compose up --build -d
   ```
   - `up` means "start the application".
   - `--build` forces Docker to read our Dockerfiles and build fresh images.
   - `-d` means "detached mode", so the terminal doesn't get locked up by the logs.

4. **Verify**: Open `http://localhost` in your browser. You should see the fully working production application!

To view the logs if something goes wrong:
```bash
docker-compose logs -f
```

To shut everything down:
```bash
docker-compose down
```
