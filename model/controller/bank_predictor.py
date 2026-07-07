"""
Bank Conflict Predictor using Historical Pattern Learning

Predicts bank conflicts and optimizes bank scheduling decisions.
"""

import logging
from typing import List, Optional, Tuple, Dict, Set
from dataclasses import dataclass, field
from collections import deque, Counter
import statistics

_logger = logging.getLogger('hbm4.bank_predictor')


@dataclass
class BankState:
    """Per-bank state tracking"""
    bank_id: int
    is_active: bool = False
    open_row: int = -1
    last_access_cycle: int = 0
    conflict_count: int = 0
    hit_count: int = 0
    miss_count: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0


@dataclass
class ConflictPrediction:
    """Bank conflict prediction result"""
    will_conflict: bool
    confidence: float
    alternative_bank: Optional[int]
    estimated_penalty_cycles: int


class BankPredictor:
    """ML-based bank conflict predictor

    Features:
    - Historical pattern learning
    - Conflict probability estimation
    - Alternative bank suggestion
    - Adaptive threshold based on workload
    """

    def __init__(
        self,
        num_banks: int = 16,
        history_size: int = 256,
        conflict_threshold: float = 0.6
    ):
        self.num_banks = num_banks
        self.conflict_threshold = conflict_threshold

        # Bank states
        self.banks: Dict[int, BankState] = {
            i: BankState(bank_id=i) for i in range(num_banks)
        }

        # Pattern tracking
        self.access_history: deque = deque(maxlen=history_size)
        self.bank_access_patterns: Dict[int, List[int]] = {i: [] for i in range(num_banks)}

        # Statistics
        self.total_predictions = 0
        self.correct_predictions = 0

    def record_access(self, bank_id: int, row_id: int, cycle: int):
        """Record a bank access for pattern learning"""
        bank = self.banks[bank_id]
        was_active = bank.is_active
        same_row = bank.open_row == row_id

        # Update bank state
        if same_row:
            bank.hit_count += 1
        else:
            bank.miss_count += 1
            bank.open_row = row_id
            bank.is_active = True

        bank.last_access_cycle = cycle

        # Update pattern history
        self.bank_access_patterns[bank_id].append(row_id)
        if len(self.bank_access_patterns[bank_id]) > 64:
            self.bank_access_patterns[bank_id].pop(0)

        self.access_history.append((bank_id, row_id, cycle))

        return same_row  # Return whether this was a row hit

    def predict_conflict(
        self,
        target_bank: int,
        target_row: int,
        current_cycle: int
    ) -> ConflictPrediction:
        """Predict if access to bank/row will cause a conflict"""
        bank = self.banks[target_bank]
        self.total_predictions += 1

        # Calculate conflict probability
        conflict_prob = self._calculate_conflict_probability(target_bank, target_row)

        # Check if current row is different
        row_conflict = bank.open_row != target_row and bank.open_row != -1

        # Estimate penalty
        penalty = self._estimate_penalty(target_bank, target_row, row_conflict)

        # Find alternative bank if conflict predicted
        alternative = None
        if conflict_prob >= self.conflict_threshold:
            alternative = self._find_alternative_bank(target_row)

        prediction = ConflictPrediction(
            will_conflict=conflict_prob >= self.conflict_threshold,
            confidence=conflict_prob,
            alternative_bank=alternative,
            estimated_penalty_cycles=penalty
        )

        if not prediction.will_conflict:
            self.correct_predictions += 1

        return prediction

    def _calculate_conflict_probability(self, bank_id: int, row_id: int) -> float:
        """Calculate conflict probability based on history"""
        # Check recent accesses to same bank
        recent = [
            (b, r) for b, r, c in self.access_history
            if b == bank_id
        ][-32:]  # Last 32 accesses

        if not recent:
            return 0.0

        # Count row changes (conflicts)
        row_changes = sum(
            1 for i in range(1, len(recent))
            if recent[i][1] != recent[i-1][1]
        )

        conflict_rate = row_changes / max(1, len(recent) - 1)

        # Check if target row matches current open row
        bank = self.banks[bank_id]
        if bank.open_row == row_id:
            return 0.0  # No conflict if same row

        return conflict_rate

    def _estimate_penalty(
        self,
        bank_id: int,
        row_id: int,
        row_conflict: bool
    ) -> int:
        """Estimate penalty cycles for conflict"""
        if not row_conflict:
            return 0

        # Base penalties from HBM4 timing
        PRECHARGE = 4
        ACTIVATE = 8
        READ_WRITE = 4

        return PRECHARGE + ACTIVATE + READ_WRITE  # ~16 cycles

    def _find_alternative_bank(self, target_row: int) -> Optional[int]:
        """Find alternative bank with same row open"""
        for bank_id, bank in self.banks.items():
            if bank.open_row == target_row and not bank.is_active:
                return bank_id
        return None

    def get_optimal_bank_order(self, request_banks: List[int]) -> List[int]:
        """Get optimal ordering of bank accesses to minimize conflicts"""
        if len(request_banks) <= 1:
            return request_banks

        # Score each bank
        scored = []
        for bank_id in request_banks:
            bank = self.banks[bank_id]
            # Higher score = better candidate for next access
            score = (
                bank.hit_rate * 0.5 +
                (bank.last_access_cycle == 0) * 0.3 +
                (not bank.is_active) * 0.2
            )
            scored.append((bank_id, score))

        # Sort by score descending (prioritize row hits)
        return [b for b, s in sorted(scored, key=lambda x: -x[1])]

    def get_bank_utilization(self) -> Dict[int, float]:
        """Get utilization percentage for each bank"""
        if not self.access_history:
            return {i: 0.0 for i in range(self.num_banks)}

        total = len(self.access_history)
        counts = Counter(b for b, r, c in self.access_history)
        return {i: counts.get(i, 0) / total for i in range(self.num_banks)}

    def get_conflict_hotspots(self) -> List[int]:
        """Get list of banks with high conflict rates"""
        hotspots = []
        for bank_id, bank in self.banks.items():
            if bank.miss_count > 10:  # Minimum threshold
                miss_rate = bank.miss_count / (bank.hit_count + bank.miss_count)
                if miss_rate > 0.5:
                    hotspots.append(bank_id)
        return hotspots

    def get_statistics(self) -> Dict:
        """Get predictor statistics"""
        accuracy = (
            self.correct_predictions / self.total_predictions
            if self.total_predictions > 0 else 0.0
        )

        return {
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions,
            'prediction_accuracy': accuracy,
            'active_banks': sum(1 for b in self.banks.values() if b.is_active),
            'hotspots': self.get_conflict_hotspots(),
            'avg_hit_rate': statistics.mean(
                b.hit_rate for b in self.banks.values()
            ),
        }

    def reset(self):
        """Reset predictor state"""
        for bank in self.banks.values():
            bank.is_active = False
            bank.open_row = -1
            bank.conflict_count = 0
            bank.hit_count = 0
            bank.miss_count = 0

        self.access_history.clear()
        for patterns in self.bank_access_patterns.values():
            patterns.clear()

        self.total_predictions = 0
        self.correct_predictions = 0
