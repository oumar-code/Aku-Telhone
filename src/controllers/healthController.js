'use strict';

function health(_req, res) {
  res.json({
    status: 'ok',
    service: 'aku-telhone',
    timestamp: new Date().toISOString(),
  });
}

module.exports = { health };
