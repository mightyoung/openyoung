import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_hello_world(client):
    """测试hello world路由"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello, World!' in response.data

def test_health_check(client):
    """测试健康检查路由"""
    response = client.get('/health')
    assert response.status_code == 200
    assert b'healthy' in response.data
    assert response.is_json
    json_data = response.get_json()
    assert json_data['status'] == 'healthy'