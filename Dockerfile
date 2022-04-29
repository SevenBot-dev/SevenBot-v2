FROM python:3.9

WORKDIR /app

# -- Install poetry
RUN pip install poetry

# -- Install requirements
COPY poetry.lock .
RUN poetry install

# -- Copy the app
COPY . .

# -- Run the app
ENV environment=production
CMD ["python", "app.py"]