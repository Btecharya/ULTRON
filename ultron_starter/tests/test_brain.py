import pytest
from ultron.brain import UltronBrain, AIError

class FakeResponse:
    def __init__(self, data): self.data = data
    def raise_for_status(self): pass
    def json(self): return self.data

class FakeSession:
    def __init__(self, data): self.data = data; self.last = None
    def post(self, url, **kwargs): self.last = (url, kwargs); return FakeResponse(self.data)

def test_local_provider_parses_answer():
    session = FakeSession({"message": {"content": "Hello from local"}})
    brain = UltronBrain("local", session=session)
    assert brain.reply([{"role":"user", "content":"Hi"}]) == "Hello from local"
    assert session.last[1]["json"]["stream"] is False

def test_unknown_provider_errors():
    with pytest.raises(AIError, match="Unknown provider"):
        UltronBrain("other").reply([])
