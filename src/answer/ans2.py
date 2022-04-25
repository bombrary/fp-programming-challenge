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


@dataclass
class InterfaceState:
    status: Status
    fail_state: FailState

    def format(self) -> list[str]:
        format_list = [ f'{period[0]} - {period[1]}' for period in self.fail_state.periods]
        if self.fail_state.fail_start is not None:
            format_list.append(f'{self.fail_state.fail_start} -')
        return format_list


def update_state(log: MonitorLog, state: InterfaceState, threshould: int):
    update_timeout_count(log, state)
    update_timeout_start(log, state)

    if state.fail_state.timeout_count >= threshould:
        # failure
        match state.status:
            case Status.FAILURE:
                pass

            case _:
                state.fail_state.start()

        state.status = Status.FAILURE

    else:
        # running
        match state.status:
            case Status.FAILURE:
                state.fail_state.end(log.date)
            
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


def failure_states(logs: list[MonitorLog], threshould: int) -> dict[IPv4Interface, InterfaceState]:
    states = dict()
    for log in sorted(logs, key=lambda log: log.date):
        if log.addr not in states:
            states[log.addr] = InterfaceState(Status.IDLE, FailState([], None, None, 0))

        update_state(log, states[log.addr], threshould)

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


def solve_as_text(src: str, threshould: int):
    logs = parse_logs_from_file(src)
    states = failure_states(logs, threshould)
    return '\n'.join(format_states(states))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help='input log file')
    parser.add_argument('N', type=int, help='threshould for timeout')
    args = parser.parse_args()

    print(solve_as_text(args.src, int(args.N)))
