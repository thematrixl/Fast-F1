import pandas as pd
import pytest

import warnings

import numpy as np

import fastf1.core
import fastf1.events


def test_get_session_deprecations():
    # deprecated kwarg 'event'
    with warnings.catch_warnings(record=True) as cap_warn:
        session = fastf1.get_session(2021, 1, event='Q')
    assert 'deprecated' in str(cap_warn[0].message)
    assert isinstance(session, fastf1.core.Session)
    assert session.name == 'Qualifying'

    # cannot supply kwargs 'identifier' and 'event' simultaneously
    with pytest.raises(ValueError):
        fastf1.get_session(2021, 1, 'Q', event='Q')

    # cannot get testing anymore
    with pytest.raises(DeprecationWarning):
        fastf1.get_session(2021, 'testing', 1)

    # getting a Weekend/Event object through get session is deprecated
    with warnings.catch_warnings(record=True) as cap_warn:
        event = fastf1.get_session(2021, 1)
    assert 'deprecated' in str(cap_warn[0].message)
    assert isinstance(event, fastf1.events.Event)


@pytest.mark.parametrize("gp", ['Bahrain', 'Bharain', 'Sakhir', 1])
@pytest.mark.parametrize("identifier", ['Q', 4, 'Qualifying'])
def test_get_session(gp, identifier):
    session = fastf1.get_session(2021, gp, identifier)
    assert session.event.event_name == 'Bahrain Grand Prix'
    assert session.name == 'Qualifying'


@pytest.mark.parametrize("test_n, pass_1", [(0, False), (1, True), (2, False)])
@pytest.mark.parametrize(
    "session_n, pass_2",
    [(0, False), (1, True), (2, True), (3, True), (4, False)]
)
def test_get_testing_session(test_n, session_n, pass_1, pass_2):
    if pass_1 and pass_2:
        session = fastf1.get_testing_session(2021, test_n, session_n)
        assert isinstance(session, fastf1.core.Session)
        assert session.name == f"Practice {session_n}"
    else:
        with pytest.raises(ValueError):
            fastf1.get_testing_session(2021, test_n, session_n)


@pytest.mark.parametrize("gp", ['Bahrain', 'Bharain', 'Sakhir', 1])
def test_get_event(gp):
    event = fastf1.get_event(2021, gp)
    assert event.event_name == 'Bahrain Grand Prix'


def test_get_event_round_zero():
    with pytest.raises(ValueError, match="testing event by round number"):
        fastf1.get_event(2021, 0)


def test_get_testing_event():
    # 0 is not a valid number for a testing event
    with pytest.raises(ValueError):
        fastf1.get_testing_event(2021, 0)

    session = fastf1.get_testing_event(2021, 1)
    assert isinstance(session, fastf1.events.Event)

    # only one testing event in 2021
    with pytest.raises(ValueError):
        fastf1.get_testing_event(2021, 2)


def test_event_schedule_partial_data_init():
    schedule = fastf1.events.EventSchedule({'event_name': ['A', 'B', 'C']})
    assert np.all([col in fastf1.events.EventSchedule._COL_TYPES.keys()
                   for col in schedule.columns])
    assert schedule.dtypes['session1'] == 'object'
    assert schedule.dtypes['session1_date'] == '<M8[ns]'


def test_event_schedule_constructor_sliced():
    schedule = fastf1.events.EventSchedule({'event_name': ['A', 'B', 'C']},
                                           year=2020)
    event = schedule.iloc[0]
    assert isinstance(event, fastf1.events.Event)
    assert event.year == 2020


def test_event_schedule_is_testing():
    schedule = fastf1.events.EventSchedule(
        {'event_format': ['conventional', 'testing']}
    )
    assert (schedule.is_testing() == [False, True]).all()


def test_event_schedule_get_event_by_round_number():
    schedule = fastf1.events.EventSchedule(
        {'event_name': ['T1', 'A', 'B', 'C', 'D'],
         'round_number': [0, 1, 2, 3, 4]}
    )
    assert schedule.get_event_by_round(2).event_name == 'B'

    with pytest.raises(ValueError, match="testing event by round number"):
        schedule.get_event_by_round(0)

    with pytest.raises(ValueError, match="Invalid round"):
        schedule.get_event_by_round(10)


def test_event_schedule_get_by_name():
    schedule = fastf1.events.EventSchedule(
        {
            'event_name': [
                'testA',
                'TESTB',
                'test_test'
            ]
        }
    )

    assert schedule.get_event_by_name('testA').event_name == 'testA'
    assert schedule.get_event_by_name('TESTA').event_name == 'testA'
    assert schedule.get_event_by_name('testb').event_name == 'TESTB'
    assert schedule.get_event_by_name('test-test').event_name == 'test_test'


def test_event_is_testing():
    assert fastf1.get_testing_event(2021, 1).is_testing()
    assert not fastf1.get_event(2021, 1).is_testing()


def test_event_get_session_name():
    event = fastf1.get_event(2021, 1)
    assert event.get_session_name(3) == 'Practice 3'
    assert event.get_session_name('Q') == 'Qualifying'
    assert event.get_session_name('praCtice 1') == 'Practice 1'


def test_event_get_session_date():
    event = fastf1.get_event(2021, 1)
    sd = event.get_session_date('Q')
    assert sd == event.session4_date
    assert isinstance(sd, pd.Timestamp)


@pytest.mark.parametrize(
    "meth_name,args,expected_name",
    [
        ['get_session', ['qualifying'], 'Qualifying'],
        ['get_session', ['R'], 'Race'],
        ['get_session', [1], 'Practice 1'],
        ['get_race', [], 'Race'],
        ['get_qualifying', [], 'Qualifying'],
        ['get_sprint', [], 'Sprint Qualifying'],
        ['get_practice', [1], 'Practice 1'],
        ['get_practice', [2], 'Practice 2'],
    ]
)
def test_event_get_session(meth_name, args, expected_name):
    event = fastf1.get_event(2021, 14)
    session = getattr(event, meth_name)(*args)
    assert session.name == expected_name