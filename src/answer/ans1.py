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


def parse_time(time_str) -> Optional[int]:
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
class InterfaceState:
    status: Status
    last_failure: Optional[datetime]
    last_running: Optional[datetime]

    def interval(self) -> str:
        if self.last_failure is not None and self.last_running is not None:
            if self.last_running > self.last_failure:
                return str((self.last_running - self.last_failure).seconds)
            else:
                return 'inf'
        elif self.last_failure is not None:
            # running is not shown -> permanently failure
            return 'inf'
        elif self.last_running is not None:
            # failure is not shown -> permanently running
            return '-'
        else:
            # illegal condition
            return 'n/a'



def is_failure(log) -> bool:
    return log.time is None


def failure_info(logs: list[MonitorLog]) -> dict[IPv4Interface, InterfaceState]:
    info = dict()
    for log in sorted(logs, key=lambda log: log.date):
        if log.addr not in info:
            info[log.addr] = InterfaceState(Status.IDLE, None, None)
        
        if is_failure(log):
            if info[log.addr].status == Status.RUNNING or info[log.addr].status == Status.IDLE:
                info[log.addr].last_failure = log.date
            info[log.addr].status = Status.FAILURE
        else:
            if info[log.addr].status == Status.FAILURE or info[log.addr].status == Status.IDLE:
                info[log.addr].last_running = log.date
            info[log.addr].status = Status.RUNNING

    return info

        

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help='input log file')
    args = parser.parse_args()

    with open(args.src, 'r') as f:
        logs = [parse_log(line) for line in f.readlines()]
        for addr, info in failure_info(logs).items():
            print(f'{addr}: {info.interval()}')
