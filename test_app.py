import pytest
from unittest.mock import patch
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.records', [
    {'grade': 1, 'school_year': '2024年度', 'title': 'Test Book 1'},
    {'grade': 2, 'school_year': '2024年度', 'title': 'Test Book 2'},
    {'grade': 1, 'school_year': '2023年度', 'title': 'Test Book 3'},
])
def test_search_endpoint(client):
    """/search エンドポイントが指定した学年のデータを正しく返すかテストする"""
    # /search?grade=1 にリクエストを送信
    response = client.get('/search?grade=1')
    assert response.status_code == 200
    
    data = response.get_json()
    
    # 1年生のデータのみが返されることを確認
    assert len(data) == 2
    assert all(item['grade'] == 1 for item in data)
    
    # 年度の降順でソートされていることを確認
    assert data[0]['title'] == 'Test Book 1' # 2024年度
    assert data[1]['title'] == 'Test Book 3' # 2023年度

    # /search?grade=3 (データなし) にリクエストを送信
    response_no_data = client.get('/search?grade=3')
    assert response_no_data.status_code == 200
    assert response_no_data.get_json() == []

    # クエリパラメータがない場合に空のリストが返されることを確認
    response_no_grade = client.get('/search')
    assert response_no_grade.status_code == 200
    assert response_no_grade.get_json() == []
