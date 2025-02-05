FROM node:23-alpine

WORKDIR /home/app

COPY package.json yarn.lock ./
RUN yarn install

COPY . .

RUN yarn build

CMD ["yarn", "dev"]