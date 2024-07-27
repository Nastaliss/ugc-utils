FROM node:20.10.0 as builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install

COPY . .

RUN npm run build

FROM nginx:1.27-alpine3.19

COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80
