FROM python:3.9

ENV HTTP_PROXY="http://de001-surf.zone2.proxy.allianz:8080/"
ENV HTTPS_PROXY="http://de001-surf.zone2.proxy.allianz:8080/"

WORKDIR /

# Install pip and required packages, and install Poetry
RUN pip install -U pip \
    && apt-get update \
    && apt install -y curl netcat \
    && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

# Add Poetry to the PATH
ENV PATH="${PATH}:/root/.poetry/bin"

# Copy application files
COPY . .

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Define the command to run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]