from typing import Optional


class LeagueConnection:
    def __init__(self):
        self.open: bool = False
        self.port: Optional[int] = None
        self.password: Optional[str] = None
