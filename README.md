# Investment Fund Management System

A microservices-based web system for managing an investment fund, its assets, employees, and investment decisions.

## Technologies

* Python
* Flask
* SQLAlchemy
* PyMongo
* PostgreSQL / SQL database
* MongoDB
* Redis
* Ethereum / Ganache
* Docker
* Kubernetes

## System Overview

The system is divided into two main parts:

* **Authentication Service** – user registration, login, JWT authentication, and account deletion.
* **Investment Fund Services** – asset management, purchase and sale orders, director approvals, reporting, and employee voting.

## User Roles

### Employee

Employees can:

* Search for assets.
* View owned and previously owned assets.
* Create purchase proposals.
* Create sale proposals.
* Vote on investment decisions using Ethereum smart contracts.

### Director

Directors can:

* View pending purchase and sale proposals.
* Approve or reject proposals.
* Initiate blockchain-based voting.
* Generate fund performance reports.

## Authentication

The authentication service uses JWT access tokens.

Available endpoints:

* `POST /register`
* `POST /login`
* `POST /delete`

## Investment Fund API

Employee endpoints:

* `POST /search`
* `POST /create_buy_order`
* `POST /create_sell_order`

Director endpoints:

* `GET /pending_orders`
* `POST /decision`
* `GET /report`

## Blockchain Voting

Investment decisions can be submitted for employee voting through Ethereum smart contracts.

The voting contract:

* Allows only predefined Ethereum addresses to vote.
* Allows each voter to vote only once.
* Supports approval and rejection votes.
* Requires an odd number of voters.
* Ends voting when a majority is reached.

Ganache is used as the local Ethereum blockchain simulator.

## Deployment

The complete system is containerized using Docker and can be deployed using Kubernetes.

Configuration is provided through Kubernetes `ConfigMap` objects, while sensitive information is stored using `Secret` objects.

The system also provides persistent storage for database services.

## Running Tests

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Run the grader tests:

```bash
pytest test_grader.py
```

## Project

This project was developed as a practical implementation of a distributed investment fund management system using containerized microservices, databases, REST APIs, and blockchain-based voting.
