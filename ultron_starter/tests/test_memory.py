from ultron.memory import ChatMemory

def test_add_and_recent_are_chronological(tmp_path):
    memory = ChatMemory(tmp_path / "chat.sqlite3")
    memory.add("user", "Hello")
    memory.add("assistant", "Hello there")
    assert memory.recent() == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hello there"},
    ]

def test_recent_limit(tmp_path):
    memory = ChatMemory(tmp_path / "chat.sqlite3")
    for i in range(5): memory.add("user", str(i))
    assert [m["content"] for m in memory.recent(2)] == ["3", "4"]

def test_clear(tmp_path):
    memory = ChatMemory(tmp_path / "chat.sqlite3")
    memory.add("user", "secret")
    memory.clear()
    assert memory.recent() == []
