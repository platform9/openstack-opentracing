
import requests

def test_jaeger_result():
    resp = requests.get('http://localhost:16686/api/traces?limit=20&lookback=1h&maxDuration&minDuration&service=Server1')
    print resp