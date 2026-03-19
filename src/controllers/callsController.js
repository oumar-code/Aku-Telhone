'use strict';

const {
  listCalls,
  getCall,
  initiateCall,
  updateCall,
} = require('../services/telephonyService');

function list(_req, res) {
  const calls = listCalls();
  res.json({ status: 'ok', count: calls.length, calls });
}

function get(req, res, next) {
  try {
    const call = getCall(req.params.id);
    res.json({ status: 'ok', call });
  } catch (err) {
    next(err);
  }
}

function initiate(req, res, next) {
  try {
    const { from, to, options } = req.body;
    const call = initiateCall(from, to, options);
    res.status(201).json({ status: 'ok', call });
  } catch (err) {
    next(err);
  }
}

function update(req, res, next) {
  try {
    const { action } = req.body;
    const call = updateCall(req.params.id, action);
    res.json({ status: 'ok', call });
  } catch (err) {
    next(err);
  }
}

module.exports = { list, get, initiate, update };
