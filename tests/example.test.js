const request = require('supertest');
const express = require('express');

const app = express();
app.get('/', (req, res) => res.send('Aku Telhone service is running!'));

describe('GET /', () => {
  it('should return service running message', async () => {
    const res = await request(app).get('/');
    expect(res.text).toBe('Aku Telhone service is running!');
  });
});
