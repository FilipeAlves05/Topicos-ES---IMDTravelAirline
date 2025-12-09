import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    load_test: {
      executor: 'constant-vus',
      vus: 10,
      duration: '5m',
      tags: { test_type: 'load_test' },
    },
  },
  thresholds: {
    'checks': ['rate>0.90'],
    'http_req_duration': ['p(95)<15000'],
  },
};

const payload = JSON.stringify({
  "flight_id": "IMD001",
  "user_id": "user_k6",
  "payment_info": {
    "card_number": "1234567890123456",
    "expiry": "12/25"
  }
});

const params = {
  headers: {
    'Content-Type': 'application/json',
  },
};

function tryParseJSON(response) {
  try {
    return response.json();
  } catch (e) {
    return null;
  }
}

export default function () {

  let url_c1 = 'http://localhost:8000/buyTicket?ft_enabled=false';
  let res_c1 = http.post(url_c1, payload, params);
  let body_c1 = tryParseJSON(res_c1);

  check(res_c1, {
    'C1: status 200-299': (r) => r.status >= 200 && r.status < 300,
    'C1: response is JSON or OK': () => body_c1 !== null || res_c1.status === 200,
  });

  let url_c2 = 'http://localhost:8000/buyTicket?ft_enabled=true';
  let res_c2 = http.post(url_c2, payload, params);
  let body_c2 = tryParseJSON(res_c2);

  check(res_c2, {
    'C2: status 200-299': (r) => r.status >= 200 && r.status < 300,
    'C2: response is JSON or OK': () => body_c2 !== null || res_c2.status === 200,
  });

  sleep(1);
}
