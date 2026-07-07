"""Thermal Heatmap Visualization

ASCII heatmap visualization for thermal distribution.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import math


@dataclass
class ThermalCell:
    """A single thermal cell"""
    row: int
    col: int
    temperature: float  # Celsius
    heat_level: float = 0.0  # 0.0 to 1.0


class ThermalHeatmap:
    """ASCII Thermal Heatmap Generator"""

    # Color characters (using ASCII substitutes)
    HEAT_CHARS = " .:-=+*#%@"
    # Cold to hot mapping

    def __init__(self, rows: int = 16, cols: int = 8):
        self.rows = rows
        self.cols = cols
        self.cells: List[List[float]] = [[0.0] * cols for _ in range(rows)]
        self.min_temp = 25.0  # Room temperature baseline
        self.max_temp = 85.0   # Maximum operating temperature

    def set_cell(self, row: int, col: int, temperature: float) -> None:
        """Set temperature for a specific cell"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.cells[row][col] = temperature

    def set_from_dict(self, data: Dict[Tuple[int, int], float]) -> None:
        """Set multiple cells from dictionary"""
        for (row, col), temp in data.items():
            self.set_cell(row, col, temp)

    def get_heat_level(self, temperature: float) -> float:
        """Convert temperature to heat level (0.0 to 1.0)"""
        if temperature <= self.min_temp:
            return 0.0
        if temperature >= self.max_temp:
            return 1.0
        return (temperature - self.min_temp) / (self.max_temp - self.min_temp)

    def _temp_to_char(self, temperature: float) -> str:
        """Convert temperature to ASCII character"""
        level = self.get_heat_level(temperature)
        char_idx = int(level * (len(self.HEAT_CHARS) - 1))
        return self.HEAT_CHARS[char_idx]

    def _format_temp(self, temperature: float) -> str:
        """Format temperature with unit"""
        return f"{temperature:5.1f}°C"

    def generate(self, show_values: bool = True) -> str:
        """Generate ASCII heatmap"""
        lines = []

        # Header
        lines.append("╔" + "═" * (self.cols * 8 + 1) + "╗")
        lines.append("║" + " THERMAL HEATMAP ".center(self.cols * 8) + "║")
        lines.append("╠" + "═" * (self.cols * 8 + 1) + "╣")

        # Column headers
        col_header = "║" + " " * 9
        for c in range(self.cols):
            col_header += f"COL{c:02d}  "
        col_header += "║"
        lines.append(col_header)
        lines.append("║" + "─" * (self.cols * 8 + 1) + "║")

        # Data rows
        for r in range(self.rows):
            row_str = f"║ ROW{r:02d} "
            for c in range(self.cols):
                temp = self.cells[r][c]
                char = self._temp_to_char(temp)
                if show_values:
                    row_str += f" {char} {temp:4.0f}°"
                else:
                    row_str += f"  {char}   "
            row_str += " ║"
            lines.append(row_str)

        # Footer with legend
        lines.append("║" + "─" * (self.cols * 8 + 1) + "║")
        legend = "║ TEMP: "
        for i, c in enumerate(self.HEAT_CHARS):
            temp = self.min_temp + (self.max_temp - self.min_temp) * i / (len(self.HEAT_CHARS) - 1)
            legend += f"{c}={temp:.0f}° "
        legend = legend[:self.cols * 8 + 8].ljust(self.cols * 8 + 9) + "║"
        lines.append(legend)
        lines.append("╚" + "═" * (self.cols * 8 + 1) + "╝")

        return "\n".join(lines)

    def generate_bank_heatmap(self, num_banks: int = 128,
                             bank_temps: Optional[List[float]] = None) -> str:
        """Generate heatmap for banks (typically 128 banks in HBM4)"""
        # 128 banks arranged in 8x16 grid
        self.rows = 8
        self.cols = 16
        self.cells = [[0.0] * self.cols for _ in range(self.rows)]

        if bank_temps and len(bank_temps) >= num_banks:
            for i, temp in enumerate(bank_temps[:num_banks]):
                row = i // self.cols
                col = i % self.cols
                self.set_cell(row, col, temp)
        else:
            # Generate sample data if not provided
            for r in range(self.rows):
                for c in range(self.cols):
                    # Simulate some hot spots
                    temp = self.min_temp + 20 + (r * 3 + c * 2) % 30
                    self.set_cell(r, c, temp)

        return self.generate(show_values=True)

    def generate_channel_heatmap(self, num_channels: int = 32) -> str:
        """Generate heatmap for channels"""
        self.rows = 1
        self.cols = num_channels
        self.cells = [[0.0] * self.cols]

        lines = []
        lines.append("╔" + "═" * (self.cols * 6 + 1) + "╗")
        lines.append("║" + " CHANNEL TEMPERATURES ".center(self.cols * 6) + "║")
        lines.append("╠" + "═" * (self.cols * 6 + 1) + "╣")

        # Channel row
        row_str = "║"
        for c in range(self.cols):
            temp = self.cells[0][c] if self.cells[0][c] > 0 else 35.0 + c * 0.5
            char = self._temp_to_char(temp)
            row_str += f"{char}{temp:4.0f}°"
        row_str += " ║"
        lines.append(row_str)

        # Channel labels
        label_str = "║  CH "
        for c in range(self.cols):
            label_str += f" {c:02d} "
        label_str += "  ║"
        lines.append(label_str)

        lines.append("╚" + "═" * (self.cols * 6 + 1) + "╝")

        return "\n".join(lines)

    def get_hotspots(self, threshold: float = 0.7) -> List[Tuple[int, int, float]]:
        """Get list of hotspots above threshold"""
        hotspots = []
        for r in range(self.rows):
            for c in range(self.cols):
                level = self.get_heat_level(self.cells[r][c])
                if level >= threshold:
                    hotspots.append((r, c, self.cells[r][c]))
        return sorted(hotspots, key=lambda x: x[2], reverse=True)

    def get_summary_stats(self) -> Dict[str, float]:
        """Get summary statistics"""
        all_temps = [self.cells[r][c] for r in range(self.rows) for c in range(self.cols)]
        if not all_temps:
            return {"min": 0, "max": 0, "avg": 0}

        return {
            "min": min(all_temps),
            "max": max(all_temps),
            "avg": sum(all_temps) / len(all_temps),
            "hotspots": len(self.get_hotspots())
        }
