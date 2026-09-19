from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseStrategy(ABC):
    def __init__(self, name: str, params: Dict[str, Any] = None):
        self.name = name
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, bars: List[Dict[str, Any]]) -> List[int]:
        """
        Generate trade signals for each bar:
        +1 = Long Entry / Hold Long
        -1 = Short Entry / Hold Short
         0 = Flat / Cash
        """
        pass

    def generate_signal_actions(self, bars: List[Dict[str, Any]]) -> List[str]:
        """
        Translates raw signals into discrete BUY, SELL, HOLD execution actions:
        - When changing from 0 to 1 -> BUY
        - When changing from 1 to 0 -> SELL
        - Otherwise -> HOLD
        """
        signals = self.generate_signals(bars)
        actions = []
        in_pos = 0

        for sig in signals:
            if sig == 1 and in_pos == 0:
                actions.append("BUY")
                in_pos = 1
            elif sig == 0 and in_pos == 1:
                actions.append("SELL")
                in_pos = 0
            else:
                actions.append("HOLD")
        return actions
