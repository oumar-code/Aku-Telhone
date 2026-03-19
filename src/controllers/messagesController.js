'use strict';

const {
  listMessages,
  getMessage,
  sendMessage,
} = require('../services/telephonyService');

function list(_req, res) {
  const msgs = listMessages();
  res.json({ status: 'ok', count: msgs.length, messages: msgs });
}

function get(req, res, next) {
  try {
    const msg = getMessage(req.params.id);
    res.json({ status: 'ok', message: msg });
  } catch (err) {
    next(err);
  }
}

function send(req, res, next) {
  try {
    const { from, to, body } = req.body;
    const msg = sendMessage(from, to, body);
    res.status(201).json({ status: 'ok', message: msg });
  } catch (err) {
    next(err);
  }
}

module.exports = { list, get, send };
