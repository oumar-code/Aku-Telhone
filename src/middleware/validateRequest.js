'use strict';

const Joi = require('joi');

const phoneNumberSchema = Joi.object({
  number: Joi.string().trim().min(7).max(20).required(),
  label: Joi.string().trim().max(64).default(''),
});

const initiateCallSchema = Joi.object({
  from: Joi.string().trim().min(7).max(20).required(),
  to: Joi.string().trim().min(7).max(20).required(),
  options: Joi.object({
    record: Joi.boolean().default(false),
  }).default({}),
});

const updateCallSchema = Joi.object({
  action: Joi.string().valid('hold', 'unhold', 'end').required(),
});

const sendMessageSchema = Joi.object({
  from: Joi.string().trim().min(7).max(20).required(),
  to: Joi.string().trim().min(7).max(20).required(),
  body: Joi.string().trim().min(1).max(1600).required(),
});

/**
 * Factory: returns an Express middleware that validates req.body against schema.
 */
function validate(schema) {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body, { abortEarly: false });
    if (error) {
      return res.status(400).json({
        status: 'error',
        message: 'Validation failed.',
        details: error.details.map((d) => d.message),
      });
    }
    req.body = value;
    return next();
  };
}

module.exports = {
  validate,
  phoneNumberSchema,
  initiateCallSchema,
  updateCallSchema,
  sendMessageSchema,
};
