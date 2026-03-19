'use strict';

const express = require('express');
const rateLimit = require('express-rate-limit');
const config = require('./config');
const routes = require('./routes');
const errorHandler = require('./middleware/errorHandler');

function createApp() {
  const app = express();

  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: false }));

  const limiter = rateLimit({
    windowMs: config.rateLimit.windowMs,
    max: config.rateLimit.max,
    standardHeaders: true,
    legacyHeaders: false,
    message: {
      status: 'error',
      message: 'Too many requests. Please try again later.',
    },
  });
  app.use(limiter);

  app.use(routes);

  // 404 handler
  app.use((_req, res) => {
    res.status(404).json({ status: 'error', message: 'Route not found.' });
  });

  app.use(errorHandler);

  return app;
}

module.exports = createApp;
