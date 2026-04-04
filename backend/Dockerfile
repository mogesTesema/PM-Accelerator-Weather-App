from python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock /app/

RUN uv pip install --system --no-root -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["guvcorn", "manage.py", "runserver", "[IP_ADDRESS]:8000"]