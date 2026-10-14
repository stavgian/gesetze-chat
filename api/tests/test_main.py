def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_retrieval_only_mode(client):
    response = client.post("/ask", json={"question": "Wann darf der Vermieter kuendigen?"})
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "retrieval_only"
    assert body["answer"] is None
    assert len(body["sources"]) == 1
    assert body["sources"][0]["section"] == "§ 573 BGB"


def test_ask_rejects_empty_question(client):
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422  # pydantic min_length validation


def test_ask_rejects_overly_long_question(client):
    response = client.post("/ask", json={"question": "a" * 10_000})
    assert response.status_code == 422
