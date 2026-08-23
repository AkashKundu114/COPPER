from app.database.models.episode import Episode, EpisodeOutcome


def test_episode_outcome_success():
    assert EpisodeOutcome.SUCCESS.value == "success"


def test_episode_outcome_partial():
    assert EpisodeOutcome.PARTIAL.value == "partial"


def test_episode_outcome_failure():
    assert EpisodeOutcome.FAILURE.value == "failure"


def test_episode_outcome_abandoned():
    assert EpisodeOutcome.ABANDONED.value == "abandoned"


def test_episode_serialization_full():
    ep = Episode(
        id=1,
        context="Coding",
        project="COPPER",
        task="Docker setup",
        goal="Configure bridge networking",
        problem="Container DNS resolution",
        decision="Used host.docker.internal",
        outcome=EpisodeOutcome.SUCCESS,
        confidence=0.92,
        tags=["docker", "networking"],
    )
    d = ep.to_dict()
    assert d["id"] == 1
    assert d["context"] == "Coding"
    assert d["project"] == "COPPER"
    assert d["outcome"] == "success"
    assert d["confidence"] == 0.92
    assert "docker" in d["tags"]
    assert "networking" in d["tags"]


def test_episode_serialization_minimal():
    ep = Episode(id=2, context="Research", task="Read paper")
    d = ep.to_dict()
    assert d["id"] == 2
    assert d["context"] == "Research"
    assert d["task"] == "Read paper"
    assert d["outcome"] is None
    assert d["created_at"] is None


def test_episode_tags_empty_default():
    ep = Episode(id=3, task="Quick test")
    d = ep.to_dict()
    assert d["tags"] == [] or d["tags"] is None
