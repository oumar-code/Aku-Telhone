'use strict';

const request = require('supertest');
const createApp = require('../src/app');
const { _reset } = require('../src/services/telephonyService');

const app = createApp();

beforeEach(() => _reset());

describe('GET /api/phone-numbers', () => {
  it('returns the list of phone numbers', async () => {
    const res = await request(app).get('/api/phone-numbers');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
    expect(Array.isArray(res.body.phoneNumbers)).toBe(true);
    expect(res.body.count).toBe(res.body.phoneNumbers.length);
    res.body.phoneNumbers.forEach((pn) => {
      expect(pn).toHaveProperty('id');
      expect(pn).toHaveProperty('number');
      expect(pn).toHaveProperty('status');
    });
  });
});

describe('GET /api/phone-numbers/:id', () => {
  it('returns a phone number by ID', async () => {
    const res = await request(app).get('/api/phone-numbers/pn-0001');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
    expect(res.body.phoneNumber.id).toBe('pn-0001');
    expect(res.body.phoneNumber.number).toBe('+14155550100');
  });

  it('returns 404 for an unknown ID', async () => {
    const res = await request(app).get('/api/phone-numbers/unknown-id');
    expect(res.statusCode).toBe(404);
    expect(res.body.status).toBe('error');
  });
});

describe('POST /api/phone-numbers', () => {
  it('registers a new phone number', async () => {
    const res = await request(app)
      .post('/api/phone-numbers')
      .send({ number: '+19995550123', label: 'Test line' });
    expect(res.statusCode).toBe(201);
    expect(res.body.status).toBe('ok');
    expect(res.body.phoneNumber.number).toBe('+19995550123');
    expect(res.body.phoneNumber.label).toBe('Test line');
    expect(res.body.phoneNumber.status).toBe('active');
  });

  it('returns 409 when number is already registered', async () => {
    const res = await request(app)
      .post('/api/phone-numbers')
      .send({ number: '+14155550100' });
    expect(res.statusCode).toBe(409);
    expect(res.body.status).toBe('error');
  });

  it('returns 400 when number is missing', async () => {
    const res = await request(app).post('/api/phone-numbers').send({});
    expect(res.statusCode).toBe(400);
    expect(res.body.status).toBe('error');
    expect(Array.isArray(res.body.details)).toBe(true);
  });
});
