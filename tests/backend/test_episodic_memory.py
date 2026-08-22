from app.database.models.episode import Episode, EpisodeOutcome

def test_episode_outcome_values():
    assert EpisodeOutcome.SUCCESS.value == 'success'
    assert EpisodeOutcome.PARTIAL.value == 'partial'
    assert EpisodeOutcome.FAILURE.value == 'failure'
    assert EpisodeOutcome.ABANDONED.value == 'abandoned'

def test_episode_to_dict():
    ep = Episode(id=1, context='Coding', project='COPPER', task='Docker setup', goal='Configure bridge networking', problem='Container DNS resolution', decision='Used host.docker.internal', outcome=EpisodeOutcome.SUCCESS, confidence=0.92, tags=['docker', 'networking'])
    d = ep.to_dict()
    assert d['id'] == 1
    assert d['context'] == 'Coding'
    assert d['project'] == 'COPPER'
    assert d['outcome'] == 'success'
    assert d['confidence'] == 0.92
    assert 'docker' in d['tags']

def test_episode_to_dict_none_outcome():
    ep = Episode(id=2, context='Research', task='Read paper')
    d = ep.to_dict()
    assert d['outcome'] is None
    assert d['created_at'] is None
