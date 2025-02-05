FROM node:23-alpine

WORKDIR /home/app

# Install yarn
RUN corepack enable

# Copy package files
COPY package.json yarn.lock* ./

# Install dependencies
RUN yarn install

# Run nuxt prepare after install
RUN yarn postinstall && yarn nuxt prepare

# Copy project files
COPY . .

# Expose port
EXPOSE 3000

# Set host to allow connections from outside container
ENV HOST=0.0.0.0
ENV PORT=3000
ENV NODE_ENV=development

# Run in development mode using yarn
CMD ["yarn", "run", "dev", "--host"]