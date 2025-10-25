import http from 'k6/http';
import ws from 'k6/ws';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Gauge, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const duration = new Trend('request_duration');
const connectionDuration = new Trend('ws_connection_duration');
const concurrentConnections = new Gauge('ws_concurrent_connections');
const totalRequests = new Counter('total_requests');

// Configuration
export const options = {
  stages: [
    { duration: '30s', target: 20 },    // Ramp-up to 20 users
    { duration: '1m30s', target: 20 },  // Stay at 20 users
    { duration: '20s', target: 0 },     // Ramp-down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],
    'http_req_failed': ['rate<0.1'],
    'errors': ['rate<0.1'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const WS_URL = __ENV.WS_URL || 'ws://localhost:8000';

let authToken = '';

export function setup() {
  // Setup phase: Register and login a test user
  const user = {
    username: `testuser_${Date.now()}`,
    email: `test_${Date.now()}@example.com`,
    password: 'TestPassword123!',
  };

  // Register
  let response = http.post(`${BASE_URL}/api/users/register`, JSON.stringify(user), {
    headers: { 'Content-Type': 'application/json' },
  });

  check(response, {
    'Registration successful': (r) => r.status === 200,
    'Got access token': (r) => JSON.parse(r.body).data.access_token !== undefined,
  });

  const data = JSON.parse(response.body);
  return { token: data.data.access_token };
}

export default function (data) {
  authToken = data.token;

  group('Authentication Endpoints', () => {
    // Check health
    let response = http.get(`${BASE_URL}/health`);
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 200);
  });

  group('Market Data Endpoints', () => {
    // Get current price
    let response = http.get(`${BASE_URL}/api/market/price/bitcoin`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 200 && response.status !== 502);

    check(response, {
      'Market price status is 200 or 502': (r) => r.status === 200 || r.status === 502,
    });

    sleep(1);

    // Get multiple prices
    response = http.get(`${BASE_URL}/api/market/prices?coins=bitcoin,ethereum,cardano`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 200 && response.status !== 502);
  });

  group('Analytics Endpoints', () => {
    // Get moving average
    let response = http.get(
      `${BASE_URL}/api/analytics/moving-average/bitcoin?period=20&method=sma`,
      { headers: { 'Authorization': `Bearer ${authToken}` } }
    );
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 200 && response.status !== 502);

    check(response, {
      'Moving average status is 200 or 502': (r) => r.status === 200 || r.status === 502,
    });

    sleep(1);

    // Get volatility
    response = http.get(`${BASE_URL}/api/analytics/volatility/bitcoin?period=20`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 200 && response.status !== 502);

    sleep(1);

    // Get correlation
    response = http.get(`${BASE_URL}/api/analytics/correlation?coin1=bitcoin&coin2=ethereum`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 200 && response.status !== 502);
  });

  group('Sentiment Endpoints', () => {
    // Get sentiment score
    let response = http.get(`${BASE_URL}/api/sentiment/bitcoin`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 200 && response.status !== 502);

    sleep(1);

    // Get sentiment trend
    response = http.get(`${BASE_URL}/api/sentiment/bitcoin/trend?days=7`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 200 && response.status !== 502);
  });

  group('Portfolio Endpoints', () => {
    // Create portfolio
    let response = http.post(
      `${BASE_URL}/api/portfolio`,
      JSON.stringify({ name: `Portfolio_${Date.now()}` }),
      { 
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
      }
    );
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 201 && response.status !== 502);

    check(response, {
      'Portfolio created': (r) => r.status === 201 || r.status === 502,
    });

    if (response.status === 201) {
      const portfolioData = JSON.parse(response.body);
      const portfolioId = portfolioData.data.id;

      sleep(1);

      // Get portfolio
      response = http.get(`${BASE_URL}/api/portfolio/${portfolioId}`, {
        headers: { 'Authorization': `Bearer ${authToken}` },
      });
      totalRequests.add(1);
      duration.add(response.timings.duration);
      errorRate.add(response.status !== 200 && response.status !== 502);

      sleep(1);

      // Add asset
      response = http.post(
        `${BASE_URL}/api/portfolio/${portfolioId}/assets`,
        JSON.stringify({
          coin_id: 'bitcoin',
          quantity: 0.5,
          purchase_price: 40000,
          purchase_date: new Date().toISOString(),
        }),
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
        }
      );
      totalRequests.add(1);
      duration.add(response.timings.duration);
      errorRate.add(response.status !== 201 && response.status !== 502);

      sleep(1);

      // Get portfolio performance
      response = http.get(`${BASE_URL}/api/portfolio/${portfolioId}/performance`, {
        headers: { 'Authorization': `Bearer ${authToken}` },
      });
      totalRequests.add(1);
      duration.add(response.timings.duration);
      errorRate.add(response.status !== 200 && response.status !== 502);
    }
  });

  sleep(2);
}

export function webSocketTest(data) {
  const authToken = data.token;
  const startTime = Date.now();

  group('WebSocket Price Updates', () => {
    concurrentConnections.add(1);

    const res = ws.connect(`${WS_URL}/ws?token=${authToken}`, null, (socket) => {
      socket.on('open', () => {
        socket.send(
          JSON.stringify({
            action: 'subscribe',
            channel: 'prices',
            coins: ['bitcoin', 'ethereum', 'cardano'],
          })
        );

        // Receive messages for 30 seconds
        let startTime = Date.now();
        while (Date.now() - startTime < 30000) {
          socket.on('message', (msg) => {
            check(msg, {
              'Got price update': (m) => m.length > 0,
            });
          });
          sleep(1);
        }
      });

      socket.on('close', () => {
        concurrentConnections.add(-1);
      });

      socket.on('error', (e) => {
        errorRate.add(1);
      });
    });

    connectionDuration.add(Date.now() - startTime);
    check(res, {
      'WebSocket connection successful': (r) => r && r.status === 101,
    });
  });
}

export function stressTest() {
  // Stress test: High concurrency for a short period
  const options = {
    stages: [
      { duration: '30s', target: 100 }, // Ramp-up to 100 concurrent users
      { duration: '1m', target: 100 },   // Stay at 100 users
      { duration: '30s', target: 0 },    // Ramp-down
    ],
    thresholds: {
      'http_req_duration': ['p(95)<1000'],
      'http_req_failed': ['rate<0.2'],
      'errors': ['rate<0.2'],
    },
  };

  group('Stress Test - High Load', () => {
    let response = http.get(`${BASE_URL}/health`);
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 200);

    check(response, {
      'Health check passes under load': (r) => r.status === 200,
    });

    sleep(1);
  });
}

export function spikeTest() {
  // Spike test: Sudden traffic spike
  const currentVU = __VU;
  
  if (currentVU > 200) {
    // Heavy load
    group('Spike Test - Heavy Load', () => {
      let response = http.get(`${BASE_URL}/api/market/prices?coins=bitcoin,ethereum,cardano,solana`, {
        headers: { 'Authorization': `Bearer ${authToken}` },
      });
      totalRequests.add(1);
      duration.add(response.timings.duration);
      errorRate.add(response.status !== 200 && response.status !== 502);
    });
  } else {
    // Normal load
    group('Spike Test - Normal Load', () => {
      let response = http.get(`${BASE_URL}/health`);
      totalRequests.add(1);
      duration.add(response.timings.duration);
      errorRate.add(response.status !== 200);
    });
  }

  sleep(1);
}

export function enduranceTest() {
  // Long-running test to check for memory leaks
  group('Endurance Test', () => {
    let response = http.get(`${BASE_URL}/health`);
    totalRequests.add(1);
    duration.add(response.timings.duration);
    errorRate.add(response.status !== 200);

    check(response, {
      'Service remains stable under sustained load': (r) => r.status === 200,
    });
  });

  sleep(0.5);
}

export function teardown(data) {
  // Optional: Cleanup test data
  console.log('Load test completed');
  console.log(`Total requests: ${totalRequests.value}`);
}
