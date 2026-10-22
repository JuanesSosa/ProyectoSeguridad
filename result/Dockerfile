# Imagen del servicio de VISUALIZACIÓN de resultados (Node.js)
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY . .

EXPOSE 80
CMD ["node", "server.js"]
