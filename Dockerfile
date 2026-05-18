FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN python -m compileall src scripts tests
CMD ["python", "scripts/hello_world_e2e.py", "--mode", "terminal", "--dry-run"]
