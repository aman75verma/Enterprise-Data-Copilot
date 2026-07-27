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

## 5. Understanding the Build Output

When you run `docker-compose up --build -d` successfully, you will see output similar to this at the end:

```
 ✔ Image enterprisedatacopilot-backend       Built               1546.6s
 ✔ Image enterprisedatacopilot-frontend      Built               1546.6s
 ✔ Network enterprisedatacopilot_copilot_net Created             0.1s   
 ✔ Container copilot-postgres                Healthy             28.1s
 ✔ Container copilot-backend                 Started             13.3s
 ✔ Container copilot-frontend                Started             15.0s  
```

### What happened here?

1. **Images Built**: Docker successfully followed the recipes in your `backend/Dockerfile` and `frontend/Dockerfile` to create the final "Images" (the packaged code). The time (e.g., `1546.6s`) indicates how long it took to download the base operating systems, install dependencies (like React packages and Python libraries), and build the code. This is usually only slow the very first time!
2. **Network Created**: Docker created a secure, private virtual network (`enterprisedatacopilot_copilot_net`) so that the containers can communicate with each other securely without being exposed to the outside internet.
3. **Containers Started**:
   - `copilot-postgres` reached a `Healthy` state. This means the database started up and passed its internal connection checks.
   - `copilot-backend` and `copilot-frontend` were successfully started and connected to the network.

### What to do next?

Now that it says `Started`, your production-grade application is actively running in the background!

1. Open your web browser and navigate to `http://localhost`.
2. You will see the Enterprise Data Copilot UI exactly as a user would see it in production.
3. Because you ran the command with the `-d` flag (detached mode), you can safely close your terminal without killing the app.
4. Try using the application. If you need to debug or see live console logs for the backend or frontend, run:
   ```bash
   docker-compose logs -f
   ```

## 6. Pushing to Docker Hub

If you want others to be able to use your application without needing to build it from the source code, you can push your built images to **Docker Hub** (the public registry for Docker images).

1. **Create an account** on [hub.docker.com](https://hub.docker.com/).
2. **Login** in your terminal:
   ```bash
   docker login
   ```
3. **Tag your images** with your Docker Hub username. For example, if your username is `johndoe`:
   ```bash
   docker tag enterprisedatacopilot-backend johndoe/copilot-backend:latest
   docker tag enterprisedatacopilot-frontend johndoe/copilot-frontend:latest
   ```
4. **Push the images**:
   ```bash
   docker push johndoe/copilot-backend:latest
   docker push johndoe/copilot-frontend:latest
   ```
Anyone in the world can now run your app by putting those image names into a `docker-compose.yml` file!

## 7. Deploying to Render (For Free)

Render is an excellent platform for hosting applications for free. Since you've already pushed your code to GitHub, Render makes it incredibly easy to go live.

> [!WARNING]  
> Render's Free tier has two limitations:
> 1. The free Postgres Database expires after 90 days.
> 2. Free Web Services (like your backend) will "go to sleep" after 15 minutes of inactivity, causing the next request to take ~50 seconds to wake up.

### Step 1: Deploy the Database
1. Go to your [Render Dashboard](https://dashboard.render.com/) and click **New -> PostgreSQL**.
2. Give it a name (e.g., `copilot-db`) and select the **Free** tier.
3. Once created, copy the **Internal Database URL**.

### Step 2: Deploy the Backend
1. In the Render Dashboard, click **New -> Web Service**.
2. Connect your GitHub repository.
3. Render will ask how to build it. Select **Docker** as the environment.
4. Set the **Dockerfile Path** to `./backend/Dockerfile`.
5. Under **Environment Variables**, add:
   - `DATABASE_URL`: (Paste the Internal Database URL from Step 1)
   - `GROQ_API_KEY`: (Your actual Groq API key)
6. Click **Create Web Service**. Once it finishes deploying, copy its public URL (e.g., `https://copilot-backend-xyz.onrender.com`).

### Step 3: Deploy the Frontend (As a Static Site)
We will deploy the frontend as a **Static Site** rather than a Docker container. This is because Render Static Sites are incredibly fast, don't sleep, and are completely free forever!

1. In the Render Dashboard, click **New -> Static Site**.
2. Connect your GitHub repository.
3. Configure the build:
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
4. Under **Environment Variables**, add:
   - `VITE_API_URL`: (Paste the public URL of your backend from Step 2)
5. Click **Create Static Site**.

**You're Live!**
Once the frontend finishes building, Render will give you a public URL for your website. It is now live on the internet!
