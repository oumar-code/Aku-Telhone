'use strict';

const request = require('supertest');
const createApp = require('../src/app');
const { _reset } = require('../src/services/telephonyService');

const app = createApp();

beforeEach(() => _reset());

describe('GET /api/messages', () => {
  it('returns the list of messages', async () => {
    const res = await request(app).get('/api/messages');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
    expect(Array.isArray(res.body.messages)).toBe(true);
    expect(res.body.count).toBe(res.body.messages.length);
    res.body.messages.forEach((m) => {
      expect(m).toHaveProperty('id');
      expect(m).toHaveProperty('from');
      expect(m).toHaveProperty('to');
      expect(m).toHaveProperty('body');
      expect(m).toHaveProperty('status');
    });
  });
});

describe('GET /api/messages/:id', () => {
  it('returns a message by ID', async () => {
    const res = await request(app).get('/api/messages/msg-0001');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
    expect(res.body.message.id).toBe('msg-0001');
    expect(res.body.message.body).toBe('Welcome to Aku Telhone!');
  });

  it('returns 404 for an unknown message ID', async () => {
    const res = await request(app).get('/api/messages/unknown-id');
    expect(res.statusCode).toBe(404);
    expect(res.body.status).toBe('error');
  });
});

describe('POST /api/messages', () => {
  it('sends a new message', async () => {
    const res = await request(app)
      .post('/api/messages')
      .send({ from: '+14155550100', to: '+13105550200', body: 'Hello from Telhone!' });
    expect(res.statusCode).toBe(201);
    expect(res.body.status).toBe('ok');
    expect(res.body.message.from).toBe('+14155550100');
    expect(res.body.message.to).toBe('+13105550200');
    expect(res.body.message.body).toBe('Hello from Telhone!');
    expect(res.body.message.status).toBe('sent');
    expect(typeof res.body.message.sentAt).toBe('string');
  });

  it('returns 400 when body is missing', async () => {
    const res = await request(app)
      .post('/api/messages')
      .send({ from: '+14155550100', to: '+13105550200' });
    expect(res.statusCode).toBe(400);
    expect(res.body.status).toBe('error');
    expect(Array.isArray(res.body.details)).toBe(true);
  });

  it('returns 400 when from is missing', async () => {
    const res = await request(app)
      .post('/api/messages')
      .send({ to: '+13105550200', body: 'Test' });
    expect(res.statusCode).toBe(400);
    expect(res.body.status).toBe('error');
  });

  it('returns 400 when to is missing', async () => {
    const res = await request(app)
      .post('/api/messages')
      .send({ from: '+14155550100', body: 'Test' });
    expect(res.statusCode).toBe(400);
    expect(res.body.status).toBe('error');
  });
});

describe('404 handler', () => {
  it('returns 404 for unknown routes', async () => {
    const res = await request(app).get('/api/unknown-endpoint');
    expect(res.statusCode).toBe(404);
    expect(res.body.status).toBe('error');
  });
});
