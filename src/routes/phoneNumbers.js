'use strict';

const router = require('express').Router();
const { list, get, register } = require('../controllers/phoneNumbersController');
const { validate, phoneNumberSchema } = require('../middleware/validateRequest');

router.get('/', list);
router.get('/:id', get);
router.post('/', validate(phoneNumberSchema), register);

module.exports = router;
