'use strict';

const router = require('express').Router();
const { list, get, send } = require('../controllers/messagesController');
const { validate, sendMessageSchema } = require('../middleware/validateRequest');

router.get('/', list);
router.get('/:id', get);
router.post('/', validate(sendMessageSchema), send);

module.exports = router;
