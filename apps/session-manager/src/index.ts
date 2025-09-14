import express from 'express';
import dotenv from 'dotenv';
import apiRoutes from './routes';
import { connectRabbitMQ } from './rabbitmq';

dotenv.config();

const app = express();
const port = process.env.PORT || 5003;

app.use(express.json());
app.use('/api/v1', apiRoutes);

async function startServer() {
  await connectRabbitMQ();

  app.listen(port, () => {
    console.log(`🚀 Session Manager service running at http://localhost:${port}`);
  });
}

startServer();
