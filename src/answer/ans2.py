from datetime import datetime
from dataclasses import dataclass
from ipaddress import IPv4Interface
from typing import Optional
from enum import Enum, auto
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
    IDLE = auto()


@dataclass
class FailState:
    period: Optional[tuple[datetime, datetime]]
    timeout_start: Optional[datetime]
    timeout_count: int


@dataclass
class InterfaceState:
    status: Status
    fail_state: FailState

    def interval(self) -> str:
        if self.status == Status.FAILURE:
            return 'inf'
        elif self.status == Status.RUNNING:
            if self.fail_state.period is not None:
                return str((self.fail_state.period[1] - self.fail_state.period[0]).seconds)
            else:
                return '-'
        else:
            return '-'


def transitState(log: MonitorLog, state: InterfaceState, threshould: int) -> InterfaceState:
    timeout_count = next_timeout_count(log, state.fail_state.timeout_count)
    timeout_start = next_timeout_start(log, state.fail_state.timeout_start, timeout_count)


    if timeout_count >= threshould:
        # failure
        match state.status:
            case Status.FAILURE:
                # failure continued
                return InterfaceState(Status.FAILURE,
                                      FailState(state.fail_state.period,
                                                timeout_start,
                                                timeout_count))
            case _:
                # failure start
                return InterfaceState(Status.FAILURE,
                                      FailState(state.fail_state.period,
                                                timeout_start,
                                                timeout_count))
    else:
        # running
        match state.status:
            case Status.RUNNING:
                # running continued
                return InterfaceState(Status.RUNNING,
                                      FailState(state.fail_state.period,
                                                timeout_start,
                                                timeout_count))
            case _:
                if state.fail_state.timeout_start is not None:
                    period = (state.fail_state.timeout_start, log.date)
                else:
                    period = None

                # revive interface
                return InterfaceState(Status.RUNNING,
                                      FailState(period,
                                                timeout_start,
                                                timeout_count))
    

def next_timeout_start(log: MonitorLog, current_date: Optional[datetime], timeout_count: int) -> Optional[datetime]:
    if timeout_count == 1:
        return log.date
    elif timeout_count == 0:
        return None
    else:
        return current_date


def next_timeout_count(log: MonitorLog, current_count: int) -> int:
    if is_timeout(log):
        return current_count + 1
    else:
        return 0


def is_timeout(log: MonitorLog) -> bool:
    return log.time is None


def failure_states(logs: list[MonitorLog], threshould: int) -> dict[IPv4Interface, InterfaceState]:
    states = dict()
    for log in sorted(logs, key=lambda log: log.date):
        if log.addr not in states:
            states[log.addr] = InterfaceState(Status.IDLE, FailState(None, None, 0))

        states[log.addr] = transitState(log, states[log.addr], threshould)

    return states


def parse_logs_from_file(path: str) -> list[MonitorLog]:
    with open(path, 'r') as f:
        logs = [parse_log(line) for line in f.readlines()]
        return logs
        

def format_failure_states(states: dict[IPv4Interface, InterfaceState]) -> list[str]:
    return [ f'{addr}: {state.interval()}' for addr, state in states.items() ]


def solve_as_text(src: str, threshould: int):
    logs = parse_logs_from_file(src)
    states = failure_states(logs, threshould)
    return '\n'.join(format_failure_states(states))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help='input log file')
    parser.add_argument('N', type=int, help='threshould for timeout')
    args = parser.parse_args()

    print(solve_as_text(args.src, int(args.N)))
