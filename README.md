# GoShow

Wing Wei Wong - B8 Cloud IT - HTW Berlin

GoShow is my final project for B8 Cloud IT. It is a concert ticket booking website where users can browse concerts, open a concert details page, book tickets, view their bookings, and manage concerts from an admin page.

Hosted website:
https://goshow-app.ashysand-7fb9ef7b.germanywestcentral.azurecontainerapps.io

Notification microservice health endpoint:
https://goshow-notification.ashysand-7fb9ef7b.germanywestcentral.azurecontainerapps.io/health

Serverless booking confirmation:
https://goshow-booking-confirmation-wingwei8.azurewebsites.net/api/booking_confirmation

## About the project

I made this project as a full-stack website. The backend is made with Python and Flask, and the frontend uses HTML, CSS, and JavaScript.

The website has these main pages:

- Home
- About
- Concerts
- Concert details
- My Bookings
- Admin

The frontend gets concert and booking data from REST API routes in the Flask backend. Users can book tickets from the concert details page, and the booking is saved in the database.

The project also has a separate notification microservice. When a booking is created, the main Flask app contacts this microservice. It also calls the Azure Function, which is used as the serverless booking confirmation part of the project.

## Cloud and containers

For the cloud part of the project, I used Microsoft Azure.

Concert images are stored in Azure Blob Storage. Concert and booking records are stored in Azure Database for PostgreSQL Flexible Server, so the data remains available when the application container is replaced. Docker images are stored in Azure Container Registry. The website and notification microservice run on Azure Container Apps.

The repository also includes Docker files, a Docker Compose file, and Kubernetes YAML files. The Kubernetes files are included for local testing with Minikube.

## Project structure

- app/app.py - main Flask app with page routes and API routes
- app/database.py - database connection, schema, and seeded concert data; PostgreSQL is used in Azure and SQLite is available for local development
- app/templates/ - HTML pages
- app/static/ - CSS and JavaScript files
- notification_service/ - separate notification microservice
- serverless/booking_confirmation/ - Azure Function for booking confirmation
- k8s/ - Kubernetes deployment and service files
- Dockerfile - Docker setup for the main app
- docker-compose.yml - local Docker Compose setup
- SOURCES.md - sources and attributions

## API routes

The frontend uses these backend routes:

| Route | Purpose |
| --- | --- |
| `GET /api/concerts` | Get the concert list |
| `GET /api/concerts/<id>` | Get one concert |
| `POST /api/concerts` | Add a concert |
| `PUT /api/concerts/<id>` | Update a concert |
| `DELETE /api/concerts/<id>` | Delete a concert |
| `GET /api/bookings` | Get the bookings |
| `POST /api/bookings` | Create a booking |
| `DELETE /api/bookings/<id>` | Cancel a booking |

When a booking is created, the API validates the input, checks the available seats, saves the booking, updates the seat count, and then contacts the notification service and Azure Function.

## Running locally

Install the Python dependencies:

- python -m venv .venv
- .\.venv\Scripts\Activate.ps1
- pip install -r requirements.txt

Start the main website:

- python app/app.py

Then open:

- http://localhost:5000

To run the notification service separately:

- python notification_service/service.py

## Running with Docker

Start the containers:

- docker compose up --build

Then open:

- http://localhost:5000

Stop the containers:

- docker compose down

## Kubernetes

The k8s folder contains Kubernetes files for running the app and notification service locally with Minikube.

Basic commands:

- minikube start
- docker build -t goshow-app:1.0 .
- docker build -t goshow-notification:1.0 ./notification_service
- minikube image load goshow-app:1.0
- minikube image load goshow-notification:1.0
- kubectl apply -f k8s/
- kubectl get pods
- kubectl get services
- minikube service goshow-app-service

Remove the resources:

- kubectl delete -f k8s/

## Serverless component

The serverless part is an Azure Function for booking confirmation.

When the function is opened directly in the browser, it returns a default example confirmation. When a real booking is made through the website, the Flask app sends the actual booking data to the function with a POST request.

Local test:

- python serverless/booking_confirmation/handler.py
