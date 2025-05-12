# Experiments Engine

Experiments Engine (ExE) enables social sector orgs with digital offerings to create and monitor experiments.

📌 For more information about the Experiments Engine, check out our [docs here](https://idinsight.github.io/experiments-engine/).


## How do I contribute to this repo as a developer?
We'd love to have people contribute to this repo. You can use the [instructions for set-up](#instructions-for-set-up) to get started!

Please note that **this repo is under active development** -- so to prevent redundant PRs / issues, please follow the following steps:
1. If you've found a bug you want to fix or want to implement a new feature, please check if it is [an existing issue](https://github.com/IDinsight/experiments-engine/issues) on the repo.
    - If it is an existing issue that has been assigned an owner, it means someone is likely already working on it, and so please wait for updates!
    - If there are no existing issues, please do create one with the appropriate labels.
2. For existing and unassigned issues, **please wait until they are marked as `priority` to start working on them**! -- since, we are actively implementing features and doing deployments for partners, we sometimes choose to take on tech debt to ensure we can push out important updates more quickly and efficiently.
3. If an unassigned issue has been marked as `priority`, assign it to yourself. Then make a feature branch and raise a PR (after making sure that the code works and relevant tests pass). **Please make sure to also fill out the details in the PR template**.

Thanks again for contributing!

## Instructions for set-up
### 1. Clone this repository:
```
git clone https://github.com/IDinsight/experiments-engine.git
```

### 2. Make environment files

Navigate to `deployment/docker-compose`. Copy the template `.env` files to create a `.base.env` and `.backend.env` files

### 3. Set-up a conda environment

Navigate to the root of this repository and run `make fresh-env`

### 4. Run the app:

  There are a couple of ways you can do this:

  #### a. For local development:

  From the root of the repository run `make run-backend`, and in a separate terminal session `make run-frontend`.

  #### b. For dev Docker deployment:

  From the root of the repository run `make dev-inst-start`. This will start the following containers:

  - _backend_: This is the container that runs the FastAPI app. You can access the Swagger UI on `localhost/api/docs` (Depending on BACKEND_ROOT_PATH in `.base.env`)
  - _caddy_: This is the container that runs Caddy reverse proxy for the app. All the requests are routed via Caddy
  - _relational_db_: Postgres DB for the ExE app
  - _frontend_: Admin app front end
  - _redis_: Redis in memory-store for the ExE app

  You will find the app running on `localhost` now. By default (based on default values in `Caddyfile` and `.base.env`) you can access

  - `https://localhost` for the frontend
  - `https://localhost/api/docs` for API documentation


  You can make changes to the "backend" or "frontend" code, and changes will be reflected instantly in the deployed containers when you save the file.

  To stop the application run `make dev-inst-stop`. To restart, run `make dev-inst-restart` after changing env variables. To restart after deleting Docker images and orphan containers, do `dev-inst-soft-reset`. To restart after deleting images, containers and volumes, do `dev-inst-hard-reset`.

  #### c. For prod Docker deployment:

  You can run `server-*` commands (following the same naming convention as for the dev Docker deployments above, for the corresponding functionality).

  There's no hot reload for prod deployments.

### 5. Explore!
Log in with the admin credentials and experiment :)
