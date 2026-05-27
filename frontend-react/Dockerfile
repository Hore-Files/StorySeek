FROM node:20-alpine

WORKDIR /app

COPY frontend-react/package*.json ./
RUN npm ci

COPY frontend-react/ ./

ENV VITE_BACKEND_URL=http://localhost:8000

EXPOSE 3001

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"]
