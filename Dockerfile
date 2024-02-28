FROM python:3.11-slim as release
RUN apt update && apt install -y git wget jq
RUN wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/bin/yq && chmod +x /usr/bin/yq

FROM mcr.microsoft.com/dotnet/sdk:6.0 AS publish
WORKDIR /src
COPY hydra-engine/hydra_engine_blazor/hydra_engine_blazor.csproj hydra_engine_blazor/
RUN dotnet restore hydra_engine_blazor/hydra_engine_blazor.csproj
COPY hydra-engine/ .
RUN dotnet publish hydra_engine_blazor/hydra_engine_blazor.csproj -c Release -o /app/publish


FROM python:3.11 as requirements-stage
EXPOSE 8080
WORKDIR /tmp
RUN pip install poetry
COPY hydra-engine/pyproject.toml hydra-engine/poetry.lock* /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM release as run
EXPOSE 8080
WORKDIR /code
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./hydra-engine/hydra_engine /code/hydra_engine
COPY --from=publish /app/publish/wwwroot /code/hydra_engine/wwwroot
RUN cp /code/hydra_engine/wwwroot/index.html /code/hydra_engine/wwwroot/404.html
COPY ./env /env
ENTRYPOINT FILES_PATH=/env python -m hydra_engine