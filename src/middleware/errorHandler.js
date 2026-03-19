'use strict';

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, _next) {
  const status = err.statusCode || err.status || 500;
  const message = err.message || 'Internal Server Error';

  if (status >= 500) {
    console.error('[ErrorHandler]', err);
  }

  res.status(status).json({
    status: 'error',
    message,
  });
}

module.exports = errorHandler;
