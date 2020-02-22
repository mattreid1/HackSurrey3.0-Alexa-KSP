# Use Node.js 12
FROM node:12

# Set the Docker working director as /usr/src/app
# Copy everything in this machines directory to Docker's /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app
RUN npm install

# Execute the command and expose port 8080
CMD node index.js
EXPOSE 8080

# docker build ./
# docker tag [hash] gcr.io/[project-id]/alexa-endpoint
# docker push gcr.io/[project-id]/alexa-endpoint