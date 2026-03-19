'use strict';

const request = require('supertest');
const createApp = require('../src/app');
const { _reset } = require('../src/services/telephonyService');

const app = createApp();

beforeEach(() => _reset());

describe('GET /api/calls', () => {
  it('returns the list of calls', async () => {
    const res = await request(app).get('/api/calls');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
    expect(Array.isArray(res.body.calls)).toBe(true);
    expect(res.body.count).toBe(res.body.calls.length);
    res.body.calls.forEach((c) => {
      expect(c).toHaveProperty('id');
      expect(c).toHaveProperty('from');
      expect(c).toHaveProperty('to');
      expect(c).toHaveProperty('status');
    });
  });
});

describe('GET /api/calls/:id', () => {
  it('returns a call by ID', async () => {
    const res = await request(app).get('/api/calls/call-0001');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
    expect(res.body.call.id).toBe('call-0001');
    expect(res.body.call.from).toBe('+14155550100');
  });

  it('returns 404 for an unknown call ID', async () => {
    const res = await request(app).get('/api/calls/unknown-id');
    expect(res.statusCode).toBe(404);
    expect(res.body.status).toBe('error');
  });
});

describe('POST /api/calls', () => {
  it('initiates a new call', async () => {
    const res = await request(app)
      .post('/api/calls')
      .send({ from: '+14155550100', to: '+13105550200' });
    expect(res.statusCode).toBe(201);
    expect(res.body.status).toBe('ok');
    expect(res.body.call.from).toBe('+14155550100');
    expect(res.body.call.to).toBe('+13105550200');
    expect(res.body.call.status).toBe('ringing');
  });

  it('respects the record option', async () => {
    const res = await request(app)
      .post('/api/calls')
      .send({ from: '+14155550100', to: '+13105550200', options: { record: true } });
    expect(res.statusCode).toBe(201);
    expect(res.body.call.record).toBe(true);
  });

  it('returns 400 when from is missing', async () => {
    const res = await request(app)
      .post('/api/calls')
      .send({ to: '+13105550200' });
    expect(res.statusCode).toBe(400);
    expect(res.body.status).toBe('error');
    expect(Array.isArray(res.body.details)).toBe(true);
  });

  it('returns 400 when to is missing', async () => {
    const res = await request(app)
      .post('/api/calls')
      .send({ from: '+14155550100' });
    expect(res.statusCode).toBe(400);
    expect(res.body.status).toBe('error');
  });
});

describe('PATCH /api/calls/:id', () => {
  it('puts an active call on hold', async () => {
    const create = await request(app)
      .post('/api/calls')
      .send({ from: '+14155550100', to: '+13105550200' });
    const callId = create.body.call.id;

    const res = await request(app)
      .patch(`/api/calls/${callId}`)
      .send({ action: 'hold' });
    expect(res.statusCode).toBe(200);
    expect(res.body.call.status).toBe('on-hold');
  });

  it('ends a call', async () => {
    const create = await request(app)
      .post('/api/calls')
      .send({ from: '+14155550100', to: '+13105550200' });
    const callId = create.body.call.id;

    const res = await request(app)
      .patch(`/api/calls/${callId}`)
      .send({ action: 'end' });
    expect(res.statusCode).toBe(200);
    expect(res.body.call.status).toBe('completed');
    expect(typeof res.body.call.endedAt).toBe('string');
    expect(typeof res.body.call.durationSeconds).toBe('number');
  });

  it('returns 409 when trying to update a completed call', async () => {
    const res = await request(app)
      .patch('/api/calls/call-0001')
      .send({ action: 'hold' });
    expect(res.statusCode).toBe(409);
    expect(res.body.status).toBe('error');
  });

  it('returns 404 for an unknown call ID', async () => {
    const res = await request(app)
      .patch('/api/calls/unknown-id')
      .send({ action: 'end' });
    expect(res.statusCode).toBe(404);
    expect(res.body.status).toBe('error');
  });

  it('returns 400 for an invalid action', async () => {
    const create = await request(app)
      .post('/api/calls')
      .send({ from: '+14155550100', to: '+13105550200' });
    const callId = create.body.call.id;

    const res = await request(app)
      .patch(`/api/calls/${callId}`)
      .send({ action: 'invalid-action' });
    expect(res.statusCode).toBe(400);
    expect(res.body.status).toBe('error');
  });
});
