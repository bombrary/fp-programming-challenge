import pytest
from answer.ans3 import InterfaceState, Status, FailState, update_state, RingBuffer, average_time, OverloadState, parse_log
from typing import Optional
from datetime import datetime


def test_ring_buffer():
    x = RingBuffer(5)
    for i in range(7):
        x.append(i)
    assert x.buf == [5, 6, 2, 3, 4]


@pytest.mark.parametrize('input, desired', [
    ([1,2], 1.5),
    ([1,2,3,4,5], (1+2+3+4+5)/5),
    ([1,2,None,4,5], None),
])
def test_average_time(input, desired):
    assert average_time(input) == desired


def make_fail_state(timeout_count=0) -> FailState:
    return FailState([], None, None, timeout_count)


def ring_buffer(size: int, buf: list[Optional[int]]) -> RingBuffer[Optional[int]]:
   assert len(buf) <= size

   rb = RingBuffer(size)
   for e in buf:
       rb.append(e)
   return rb


@pytest.mark.parametrize('fail_th, ol_cnt, ol_th, state, log, desired', [
    # wether the time pushed (1)
    (100, 5, 100,
     InterfaceState(Status.RUNNING, make_fail_state(), OverloadState([], None, ring_buffer(5, []))),
     parse_log('20220101000000,1.1.1.1/30,1'),
     InterfaceState(Status.RUNNING, make_fail_state(), OverloadState([], None, ring_buffer(5, [1])))),

    # wether the time pushed (2)
    (100, 5, 100,
     InterfaceState(Status.RUNNING,
                    FailState([], None, None, 0),
                    OverloadState([], None, ring_buffer(5, []))),
     parse_log('20220101000000,1.1.1.1/30,-'),
     InterfaceState(Status.OVERLOAD,
                    FailState([], None, datetime(2022, 1, 1), 1),
                    OverloadState([], datetime(2022, 1, 1), ring_buffer(5, [None])))),

    # overload started
    (100, 5, 2.5,
     InterfaceState(Status.RUNNING,
                    make_fail_state(),
                    OverloadState([], None, ring_buffer(5, [1,2,3]))),
     parse_log('20220101000000,1.1.1.1/30,4'),
     InterfaceState(Status.OVERLOAD,
                    make_fail_state(),
                    OverloadState([], datetime(2022, 1, 1), ring_buffer(5, [1,2,3,4])))),

    # overload continued
    (100, 5, 2.5,
     InterfaceState(Status.OVERLOAD,
                    make_fail_state(),
                    OverloadState([], datetime(2021, 12, 31), ring_buffer(5, [1,2,3,4]))),
     parse_log('20220101000000,1.1.1.1/30,4'),
     InterfaceState(Status.OVERLOAD,
                    make_fail_state(),
                    OverloadState([], datetime(2021, 12, 31), ring_buffer(5, [1,2,3,4,4])))),

    # overload ended
    (100, 5, 2.5,
     InterfaceState(Status.OVERLOAD,
                    make_fail_state(),
                    OverloadState([],
                                  datetime(2021, 12, 31),
                                  ring_buffer(5, [1,2,3,4]))),
     parse_log('20220101000000,1.1.1.1/30,0'),
     InterfaceState(Status.RUNNING,
                    make_fail_state(),
                    OverloadState([(datetime(2021, 12, 31), datetime(2022, 1, 1))],
                                  None,
                                  ring_buffer(5, [1,2,3,4,0])))),

    # overload ended and failure start
    (3, 5, 2.5,
     InterfaceState(Status.OVERLOAD,
                    FailState([], None, datetime(2021, 12, 30), 2),
                    OverloadState([],
                                  datetime(2021, 12, 25),
                                  ring_buffer(5, [1,None,None]))),
     parse_log('20220101000000,1.1.1.1/30,-'),
     InterfaceState(Status.FAILURE,
                    FailState([], datetime(2021, 12, 30), None, 3),
                    OverloadState([(datetime(2021, 12, 25), datetime(2021, 12, 30))],
                                  None,
                                  ring_buffer(5, [1,None,None,None])))),

    # failure ended and overload revived
    (3, 5, 2.5,
     InterfaceState(Status.FAILURE,
                    FailState([], datetime(2021, 12, 31), None, 3),
                    OverloadState([],
                                  None,
                                  ring_buffer(5, [1,None,None,None]))),
     parse_log('20220101000000,1.1.1.1/30,1'),
     InterfaceState(Status.OVERLOAD,
                    FailState([(datetime(2021, 12, 31), datetime(2022, 1, 1))], None, None, 0),
                    OverloadState([],
                                  datetime(2022, 1, 1),
                                  ring_buffer(5, [1,None,None,None,1])))),
])
def test_transition(fail_th, ol_cnt, ol_th, state, log, desired):
    # check errors of the test case
    assert state.overload_state.times.size == ol_cnt
    assert desired.overload_state.times.size == ol_cnt

    update_state(log, state, fail_th, ol_cnt, ol_th)
    assert state.status == desired.status
    assert state.fail_state == desired.fail_state
    assert state.overload_state == desired.overload_state

