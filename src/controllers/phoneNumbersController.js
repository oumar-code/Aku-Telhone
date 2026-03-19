'use strict';

const {
  listPhoneNumbers,
  getPhoneNumber,
  registerPhoneNumber,
} = require('../services/telephonyService');

function list(_req, res) {
  const numbers = listPhoneNumbers();
  res.json({ status: 'ok', count: numbers.length, phoneNumbers: numbers });
}

function get(req, res, next) {
  try {
    const pn = getPhoneNumber(req.params.id);
    res.json({ status: 'ok', phoneNumber: pn });
  } catch (err) {
    next(err);
  }
}

function register(req, res, next) {
  try {
    const { number, label } = req.body;
    const pn = registerPhoneNumber(number, label);
    res.status(201).json({ status: 'ok', phoneNumber: pn });
  } catch (err) {
    next(err);
  }
}

module.exports = { list, get, register };
