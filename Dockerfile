FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY hydra_engine_blazor/hydra_engine_blazor.csproj .
RUN dotnet restore hydra_engine_blazor.csproj
COPY . .
RUN dotnet build hydra_engine_blazor/hydra_engine_blazor.csproj -c Release -o /app/build

FROM build AS publish
RUN dotnet publish hydra_engine_blazor/hydra_engine_blazor.csproj -c Release -o /app/publish



FROM python:3.11 as requirements-stage
EXPOSE 8080
#
WORKDIR /tmp

#
RUN pip install poetry

#
COPY ./pyproject.toml ./poetry.lock* /tmp/

#
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

#
FROM python:3.11-alpine as run

#
WORKDIR /code

#
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY --from=publish /app/publish/wwwroot /code/wwwroot
RUN cp /code/wwwroot/index.html /code/wwwroot/404.html
COPY ./hydra_engine /code/hydra_engine
CMD python -m hydra_engine