"""
DYR Parser: Extract dynamic model data from PSSE .dyr files.

Lightweight parser that doesn't require ANDES — reads .dyr files
directly into structured Python objects.
"""

from pathlib import Path
from dataclasses import dataclass, field
import re


@dataclass
class DynamicModelEntry:
    """A single dynamic model entry from a .dyr file."""
    bus: int
    model_name: str
    machine_id: str
    parameters: list[float] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> dict[str, float]:
        """Convert positional parameters to a named dict using model registry."""
        from .model_registry import get_mapping
        mapping = get_mapping(self.model_name)
        if mapping is None:
            return {f"p{i}": v for i, v in enumerate(self.parameters)}

        result = {}
        for i, pm in enumerate(mapping.parameters):
            if i < len(self.parameters):
                result[pm.psse_name] = self.parameters[i]
        return result


@dataclass
class DYRFile:
    """Parsed PSSE .dyr file."""
    path: Path
    models: list[DynamicModelEntry] = field(default_factory=list)
    model_types: set[str] = field(default_factory=set)

    def get_models_by_type(self, model_name: str) -> list[DynamicModelEntry]:
        """Get all entries for a specific model type."""
        return [m for m in self.models if m.model_name == model_name.upper().strip()]

    def get_models_by_bus(self, bus: int) -> list[DynamicModelEntry]:
        """Get all dynamic models connected to a specific bus."""
        return [m for m in self.models if m.bus == bus]

    def get_bus_model_map(self) -> dict[int, list[str]]:
        """Get mapping of bus → list of model types."""
        result: dict[int, list[str]] = {}
        for m in self.models:
            result.setdefault(m.bus, []).append(m.model_name)
        return result

    def summary(self) -> dict:
        """Get summary statistics of the .dyr file."""
        return {
            "total_entries": len(self.models),
            "model_types": sorted(self.model_types),
            "model_counts": {mt: len(self.get_models_by_type(mt)) for mt in sorted(self.model_types)},
            "buses_with_dynamics": sorted(set(m.bus for m in self.models)),
        }


def parse_dyr(dyr_path: str | Path) -> DYRFile:
    """Parse a PSSE .dyr file into structured data.

    .dyr format:
        <bus> '<model_name>' <machine_id> <param1> <param2> ... /
    
    Each model entry can span multiple lines, terminated by '/'.
    """
    path = Path(dyr_path)
    content = path.read_text()

    models = []
    model_types = set()

    # Split into entries (each terminated by '/')
    # An entry starts with: <number> '<model_name>'
    # Model name may have trailing spaces in the quotes (e.g., 'EXDC2 ')
    entry_pattern = re.compile(
        r"(\d+)\s+'([^']+)'\s+(\S+)(.*?)/",
        re.DOTALL
    )

    for match in entry_pattern.finditer(content):
        bus = int(match.group(1))
        model_name = match.group(2).upper().strip()  # strip trailing spaces like 'EXDC2 '
        machine_id = match.group(3)
        params_text = match.group(4).strip()
        raw_text = match.group(0).strip()

        # Parse parameters from the remaining text
        params = []
        for token in params_text.split():
            token = token.strip()
            if not token:
                continue
            try:
                # Handle Fortran scientific notation: 0.20000E-01
                val = float(token.replace('D', 'E').replace('d', 'e'))
                params.append(val)
            except ValueError:
                # Might be a Line 'Toggle' entry or similar
                continue

        entry = DynamicModelEntry(
            bus=bus,
            model_name=model_name,
            machine_id=machine_id,
            parameters=params,
            raw_text=raw_text,
        )
        models.append(entry)
        model_types.add(model_name)

    return DYRFile(path=path, models=models, model_types=model_types)
