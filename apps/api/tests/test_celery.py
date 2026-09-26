from app.workers.tasks import ping, refresh_holding_prices


def test_celery_ping_task():
    result = ping()
    assert result == "pong"


def test_celery_refresh_holding_prices_task():
    result = refresh_holding_prices()
    assert result["status"] == "ok"
