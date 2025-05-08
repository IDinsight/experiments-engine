## Deploying using docker compose

The simplest way to deploy the application is using docker compose. The following steps will guide you through the process.

!!! warning "Ensure you have [Docker](https://docs.docker.com/get-docker/) installed"

**Step 1:** Clone the [ExE repository](https://github.com/IDinsight/experiments-engine).

```shell
git clone git@github.com:IDinsight/experiments-engine.git
```

**Step 2:** Navigate to the `deployment/docker-compose/` subfolder.

```shell
cd deployment/docker-compose/
```

**Step 3:** Copy `template.*.env` files to `.*.env`:

```shell
cp template.base.env .base.env
cp template.backend.env .backend.env
```

Edit the `.base.env` and `.backend.env` files to set the environment variables.

**Step 4:** Run docker-compose

```shell
docker compose -f docker-compose.yml -p exe-stack up -d --build
```

You can now view the ExE app at `https://$DOMAIN/` (by default, this should be [https://localhost/](https://localhost/)) and the API documentation at
`https://$DOMAIN/api/docs` (you can also test the endpoints here).

**Step 5:** Shutdown containers

```shell
docker compose -f docker-compose.yml -f docker-compose.dev.yml -p exe-stack down
```
