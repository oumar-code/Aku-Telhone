'use strict';

let _counter = 0;

/**
 * Generates a simple unique ID suffix without external dependencies.
 * @returns {string}
 */
function _genId() {
  _counter += 1;
  return `${Date.now().toString(36)}-${_counter.toString(36)}`;
}

/**
 * In-memory stores. In a production deployment these would be backed
 * by a database or an external telephony provider (e.g. Twilio, Vonage).
 */
let phoneNumbers = [
  {
    id: 'pn-0001',
    number: '+14155550100',
    label: 'Support line',
    status: 'active',
    createdAt: '2026-01-01T00:00:00.000Z',
  },
  {
    id: 'pn-0002',
    number: '+14155550101',
    label: 'Sales line',
    status: 'active',
    createdAt: '2026-01-02T00:00:00.000Z',
  },
];

let calls = [
  {
    id: 'call-0001',
    from: '+14155550100',
    to: '+12125550200',
    status: 'completed',
    record: false,
    startedAt: '2026-01-01T10:00:00.000Z',
    endedAt: '2026-01-01T10:05:30.000Z',
    durationSeconds: 330,
  },
];

let messages = [
  {
    id: 'msg-0001',
    from: '+14155550100',
    to: '+12125550200',
    body: 'Welcome to Aku Telhone!',
    status: 'delivered',
    sentAt: '2026-01-01T09:00:00.000Z',
  },
];

/* ─────────────── Phone Numbers ─────────────── */

/**
 * Returns all registered phone numbers.
 * @returns {object[]}
 */
function listPhoneNumbers() {
  return phoneNumbers;
}

/**
 * Returns a single phone number by ID.
 * @param {string} id
 * @returns {object}
 */
function getPhoneNumber(id) {
  const pn = phoneNumbers.find((p) => p.id === id);
  if (!pn) {
    const err = new Error(`Phone number '${id}' not found.`);
    err.statusCode = 404;
    throw err;
  }
  return pn;
}

/**
 * Registers a new phone number.
 * @param {string} number  E.164-style phone number
 * @param {string} label   Optional label
 * @returns {object}
 */
function registerPhoneNumber(number, label = '') {
  const existing = phoneNumbers.find((p) => p.number === number);
  if (existing) {
    const err = new Error(`Phone number '${number}' is already registered.`);
    err.statusCode = 409;
    throw err;
  }
  const pn = {
    id: `pn-${_genId()}`,
    number,
    label,
    status: 'active',
    createdAt: new Date().toISOString(),
  };
  phoneNumbers.push(pn);
  return pn;
}

/* ─────────────── Calls ─────────────── */

/**
 * Returns all calls.
 * @returns {object[]}
 */
function listCalls() {
  return calls;
}

/**
 * Returns a single call by ID.
 * @param {string} id
 * @returns {object}
 */
function getCall(id) {
  const call = calls.find((c) => c.id === id);
  if (!call) {
    const err = new Error(`Call '${id}' not found.`);
    err.statusCode = 404;
    throw err;
  }
  return call;
}

/**
 * Initiates a new call.
 * @param {string} from
 * @param {string} to
 * @param {object} options
 * @returns {object}
 */
function initiateCall(from, to, options = {}) {
  const call = {
    id: `call-${_genId()}`,
    from,
    to,
    status: 'ringing',
    record: options.record || false,
    startedAt: new Date().toISOString(),
    endedAt: null,
    durationSeconds: null,
  };
  calls.push(call);
  return call;
}

/**
 * Updates an active call (hold / unhold / end).
 * @param {string} id
 * @param {string} action  'hold' | 'unhold' | 'end'
 * @returns {object}
 */
function updateCall(id, action) {
  const call = getCall(id);

  if (call.status === 'completed') {
    const err = new Error(`Call '${id}' has already ended.`);
    err.statusCode = 409;
    throw err;
  }

  if (action === 'hold') {
    call.status = 'on-hold';
  } else if (action === 'unhold') {
    call.status = 'in-progress';
  } else if (action === 'end') {
    call.status = 'completed';
    call.endedAt = new Date().toISOString();
    call.durationSeconds = Math.floor(
      (new Date(call.endedAt) - new Date(call.startedAt)) / 1000
    );
  }

  return call;
}

/* ─────────────── Messages ─────────────── */

/**
 * Returns all messages.
 * @returns {object[]}
 */
function listMessages() {
  return messages;
}

/**
 * Returns a single message by ID.
 * @param {string} id
 * @returns {object}
 */
function getMessage(id) {
  const msg = messages.find((m) => m.id === id);
  if (!msg) {
    const err = new Error(`Message '${id}' not found.`);
    err.statusCode = 404;
    throw err;
  }
  return msg;
}

/**
 * Sends a new SMS message.
 * @param {string} from
 * @param {string} to
 * @param {string} body
 * @returns {object}
 */
function sendMessage(from, to, body) {
  const msg = {
    id: `msg-${_genId()}`,
    from,
    to,
    body,
    status: 'sent',
    sentAt: new Date().toISOString(),
  };
  messages.push(msg);
  return msg;
}

/* ─────────────── Test helpers ─────────────── */

/**
 * Resets in-memory stores to initial seed data.
 * Used by tests to get a clean state.
 */
function _reset() {
  phoneNumbers = [
    {
      id: 'pn-0001',
      number: '+14155550100',
      label: 'Support line',
      status: 'active',
      createdAt: '2026-01-01T00:00:00.000Z',
    },
    {
      id: 'pn-0002',
      number: '+14155550101',
      label: 'Sales line',
      status: 'active',
      createdAt: '2026-01-02T00:00:00.000Z',
    },
  ];
  calls = [
    {
      id: 'call-0001',
      from: '+14155550100',
      to: '+12125550200',
      status: 'completed',
      record: false,
      startedAt: '2026-01-01T10:00:00.000Z',
      endedAt: '2026-01-01T10:05:30.000Z',
      durationSeconds: 330,
    },
  ];
  messages = [
    {
      id: 'msg-0001',
      from: '+14155550100',
      to: '+12125550200',
      body: 'Welcome to Aku Telhone!',
      status: 'delivered',
      sentAt: '2026-01-01T09:00:00.000Z',
    },
  ];
}

module.exports = {
  listPhoneNumbers,
  getPhoneNumber,
  registerPhoneNumber,
  listCalls,
  getCall,
  initiateCall,
  updateCall,
  listMessages,
  getMessage,
  sendMessage,
  _reset,
};
