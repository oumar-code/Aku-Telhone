'use strict';

const router = require('express').Router();

router.get('/', (_req, res) => res.send('Aku Telhone service is running!'));

router.use('/health', require('./health'));
router.use('/api/phone-numbers', require('./phoneNumbers'));
router.use('/api/calls', require('./calls'));
router.use('/api/messages', require('./messages'));

module.exports = router;
