'use strict';

const request = require('supertest');
const createApp = require('../src/app');

const app = createApp();

describe('GET /health', () => {
  it('returns 200 with status ok', async () => {
    const res = await request(app).get('/health');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
    expect(res.body.service).toBe('aku-telhone');
    expect(typeof res.body.timestamp).toBe('string');
  });
});
