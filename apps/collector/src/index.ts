import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import apiRoutes from './routes';
import { connectRabbitMQ } from './rabbitmq';

// Load environment variables from .env file
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// --- Middleware ---
// Enable Cross-Origin Resource Sharing
app.use(cors());
// Parse JSON bodies (for /api/v1/data)
app.use(express.json({ limit: '10mb' }));
// Parse URL-encoded bodies (for multipart/form-data fields)
app.use(express.urlencoded({ extended: true }));

// --- API Routes ---
// Mount all API routes under the /api/v1 prefix
app.use('/api/v1', apiRoutes);

// --- Server Startup ---
async function startServer() {
  // First, connect to RabbitMQ
  await connectRabbitMQ();

  // Then, start the Express server
  app.listen(PORT, () => {
    console.log(`🚀 Collector service is running on http://localhost:${PORT}`);
  });
}

startServer().catch((error) => {
  console.error('❌ Failed to start the server:', error);
  process.exit(1);
});
