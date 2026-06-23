FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build for production
RUN npm run build

# Expose port
EXPOSE 3000

# Serve with preview (or use nginx for production)
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
