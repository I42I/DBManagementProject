FROM node:18-alpine AS frontend
WORKDIR /frontend

ENV npm_config_unsafe_perm=true

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN chmod +x node_modules/.bin/* && npm run build

FROM python:3.13-alpine
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend /frontend/dist ./static

ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]