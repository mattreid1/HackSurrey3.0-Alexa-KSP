# Use Node.js 12
FROM node:12

# Set the Docker working director as /usr/src/app
# Copy everything in this machines directory to Docker's /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app
RUN npm install

# Execute the command and expose port 80
CMD node index.js
EXPOSE 80

# docker build -t gcr.io/alexa-kerbal/websocket ./
# docker push gcr.io/alexa-kerbal/websocket