'use strict';

const router = require('express').Router();

router.use('/health', require('./health'));
router.use('/api/phone-numbers', require('./phoneNumbers'));
router.use('/api/calls', require('./calls'));
router.use('/api/messages', require('./messages'));

module.exports = router;
