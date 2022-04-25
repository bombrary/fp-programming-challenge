from datetime import datetime
from dataclasses import dataclass
from ipaddress import IPv4Interface
from typing import Optional
from enum import Enum, auto
from typing import TypeVar, Generic
import argparse


@dataclass
class MonitorLog:
    date: datetime
    addr: IPv4Interface
    time: Optional[int]


def parse_time(time_str: str) -> Optional[int]:
    try:
        return int(time_str)
    except ValueError:
        return None
    

def parse_log(line: str) -> MonitorLog:
    [date_str, addr_str, time_str] = line.split(',')
    date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
    addr = IPv4Interface(addr_str)
    time = parse_time(time_str)

    return MonitorLog(date, addr, time)


class Status(Enum):
    RUNNING = auto()
    FAILURE = auto()
    OVERLOAD = auto()
    IDLE = auto()


T = TypeVar('T')

class RingBuffer(Generic[T]):
    def __init__(self, size):
        self.size = size
        self.idx = 0
        self.buf = []

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return f'<RingBuffer size={self.size}, {self.buf}, idx={self.idx}, ave={average_time(self.buf)}>'

    def append(self, x: T):
        if len(self.buf) < self.size:
            self.buf.append(x)
        else:
            self.buf[self.idx] = x

        self.idx = (self.idx + 1) % self.size


def average_time(time_list: list[Optional[int]]) -> Optional[float]:
    if time_list == []:
        return 0

    time_sum = 0
    for t in time_list:
        if t is None:
            return None
        else:
            time_sum += t
    return time_sum / len(time_list)


@dataclass
class OverloadState:
    periods: list[tuple[datetime, datetime]]
    overload_start: Optional[datetime]
    # if None then timeout, REGARDED AS INF, and so that causes overload.
    times: RingBuffer[Optional[int]]

    def format(self):
        if self.periods != []:
            last_period = self.periods[-1]
            return f'{last_period[0]} - {last_period[1]}'
        elif self.overload_start is not None:
            return f'{self.overload_start} -'
        else:
            return 'n/a'

    def end(self, overload_end: datetime):
        if self.overload_start is not None:
            self.periods.append((self.overload_start, overload_end))
            self.overload_start = None

    def start(self, overload_start: datetime):
        self.overload_start = overload_start
    


@dataclass
class FailState:
    periods: list[tuple[datetime, datetime]]
    fail_start: Optional[datetime]
    timeout_start: Optional[datetime]
    timeout_count: int

    def start(self):
        self.fail_start = self.timeout_start
        self.timeout_start = None

    def end(self, fail_end: datetime):
        if self.fail_start is not None:
            self.periods.append((self.fail_start, fail_end))
            self.fail_start = None

    def format(self):
        if self.periods != []:
            last_period = self.periods[-1]
            return f'{last_period[0]} - {last_period[1]}'
        elif self.fail_start is not None:
            return f'{self.fail_start} -'
        else:
            return 'n/a'


@dataclass
class InterfaceState:
    status: Status
    fail_state: FailState
    overload_state: OverloadState

    def format(self) -> list[str]:
        periods = [('FAILURE ', period) for period in self.fail_state.periods] + \
            [('OVERLOAD', period) for period in self.overload_state.periods]

        periods.sort(key=lambda x: x[1])

        format_list = [ f'{status}({period[0]} - {period[1]})' for status, period in periods]
        if self.fail_state.fail_start is not None:
            format_list.append(f'FAILURE ({self.fail_state.fail_start} -)')

        if self.overload_state.overload_start is not None:
            format_list.append(f'OVERLOAD({self.overload_state.overload_start} -)')

        return format_list


def update_state(log: MonitorLog,
                 state: InterfaceState,
                 fail_threshould: int,
                 overload_count: int,
                 overload_threshould: float):
    update_timeout_count(log, state)
    update_timeout_start(log, state)

    state.overload_state.times.append(log.time)
    ave_time = average_time(state.overload_state.times.buf)

    if state.fail_state.timeout_count >= fail_threshould:
        # failure
        match state.status:
            case Status.FAILURE:
                pass

            case Status.OVERLOAD:
                # for fear of overlap of periods of overload and failure
                timeout_start = state.fail_state.timeout_start
                overload_start = state.overload_state.overload_start
                if timeout_start is not None \
                    and overload_start is not None \
                    and overload_start < timeout_start:
                    state.overload_state.end(timeout_start)
                else:
                    state.overload_state.overload_start = None

                state.fail_state.start()

            case _:
                state.fail_state.start()

        state.status = Status.FAILURE

    elif ave_time is None or ave_time >= overload_threshould:
        # overload
        match state.status:
            case Status.OVERLOAD:
                pass

            case Status.FAILURE:
                state.fail_state.end(log.date)
                state.overload_state.start(log.date)

            case _:
                state.overload_state.start(log.date)

        state.status = Status.OVERLOAD
    else:
        # running
        match state.status:
            case Status.FAILURE:
                state.fail_state.end(log.date)

            case Status.OVERLOAD:
                state.overload_state.end(log.date)
            
            case _:
                pass

        state.status = Status.RUNNING


def update_timeout_count(log: MonitorLog, state: InterfaceState):
    if is_timeout(log):
        state.fail_state.timeout_count += 1
    else:
        state.fail_state.timeout_count = 0


def update_timeout_start(log: MonitorLog, state: InterfaceState):
    fail_state = state.fail_state
    if fail_state.timeout_count == 1 and fail_state.fail_start is None:
        fail_state.timeout_start = log.date
    elif fail_state.timeout_count == 0:
        fail_state.timeout_start = None



def is_timeout(log: MonitorLog) -> bool:
    return log.time is None


def interface_states(logs: list[MonitorLog],
                   fail_threshould: int,
                   overload_count: int,
                   overload_threshould: float) -> dict[IPv4Interface, InterfaceState]:
    states = dict()
    for log in sorted(logs, key=lambda log: log.date):
        if log.addr not in states:
            states[log.addr] = InterfaceState(Status.IDLE,
                                              FailState([], None, None, 0),
                                              OverloadState([], None, RingBuffer(overload_count)))

        update_state(log, states[log.addr], fail_threshould, overload_count, overload_threshould)

    return states


def parse_logs_from_file(path: str) -> list[MonitorLog]:
    with open(path, 'r') as f:
        logs = [parse_log(line) for line in f.readlines()]
        return logs
        

def format_states(states: dict[IPv4Interface, InterfaceState]) -> list[str]:
    format_list = []
    for addr, state in states.items():
        state_format = '\n  '.join(state.format())
        format_list.append(f'{addr}:\n  {state_format}')

    return format_list


def solve_as_text(src: str, threshould: int, overload_count: int, overload_threshould: float):
    logs = parse_logs_from_file(src)
    states = interface_states(logs, threshould, overload_count, overload_threshould)
    return '\n'.join(format_states(states))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help='input log file')
    parser.add_argument('N', type=int, help='threshould for timeout')
    parser.add_argument('M', type=int, help='number of time to response')
    parser.add_argument('t', type=float, help='threshould for overload')
    args = parser.parse_args()

    print(solve_as_text(args.src, int(args.N), int(args.M), float(args.t)))
