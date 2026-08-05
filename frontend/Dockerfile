FROM node:20-alpine

WORKDIR /app

# Copy only the manifests first so npm install stays cached across rebuilds
# unless the dependency list itself changes.
COPY package.json package-lock.json ./
RUN npm install

COPY . .

EXPOSE 5173

# --host is required: Vite's dev server binds to localhost by default, which
# is unreachable from outside the container without it.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
