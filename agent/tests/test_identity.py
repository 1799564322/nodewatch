from nodewatch_agent.identity import load_or_create_instance_id


def test_instance_id_is_persisted(tmp_path) -> None:
    path = tmp_path / "state" / "identity.json"
    first = load_or_create_instance_id(path)
    second = load_or_create_instance_id(path)
    assert first == second
