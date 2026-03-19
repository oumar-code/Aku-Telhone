'use strict';

const router = require('express').Router();
const { list, get, initiate, update } = require('../controllers/callsController');
const {
  validate,
  initiateCallSchema,
  updateCallSchema,
} = require('../middleware/validateRequest');

router.get('/', list);
router.get('/:id', get);
router.post('/', validate(initiateCallSchema), initiate);
router.patch('/:id', validate(updateCallSchema), update);

module.exports = router;
