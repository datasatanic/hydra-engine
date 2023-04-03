FROM python:3.11-alpine as release
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/edge/community' >> /etc/apk/repositories && \
    echo 'http://dl-cdn.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories
RUN apk update && apk add git terragrunt terraform graphviz


FROM mcr.microsoft.com/dotnet/sdk:6.0 AS publish
WORKDIR /src
COPY hydra_engine_blazor/hydra_engine_blazor.csproj .
RUN dotnet restore hydra_engine_blazor.csproj
COPY . .
RUN dotnet publish hydra_engine_blazor/hydra_engine_blazor.csproj -c Release -o /app/publish


FROM python:3.11 as requirements-stage
EXPOSE 8080
WORKDIR /tmp
RUN pip install poetry
COPY ./pyproject.toml ./poetry.lock* /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM release as run
EXPOSE 8080
WORKDIR /code
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY --from=publish /app/publish/wwwroot /code/wwwroot
RUN cp /code/wwwroot/index.html /code/wwwroot/404.html
COPY ./hydra_engine /code/hydra_engine
CMD python -m hydra_engine