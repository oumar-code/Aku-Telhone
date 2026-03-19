'use strict';

const createApp = require('./app');
const config = require('./config');

const app = createApp();

app.listen(config.port, () => {
  console.log(`[aku-telhone] Server running on port ${config.port} (${config.nodeEnv})`);
});

module.exports = app;
