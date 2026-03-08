"""
Evolver - Self-evolution system
Based on OpenClaw GEP protocol
"""

import uuid
from datetime import datetime
from pathlib import Path

import yaml

from .models import (
    Capsule,
    EvolutionEvent,
    EvolutionEventType,
    Gene,
    GeneCategory,
    Personality,
)


class GeneMatcher:
    """Gene matcher - matches signals to genes"""

    def __init__(self, genes: list[Gene] = None):
        self._genes: dict[str, Gene] = {}
        if genes:
            for gene in genes:
                self._genes[gene.id] = gene

    def register_gene(self, gene: Gene):
        self._genes[gene.id] = gene

    def match_signals(self, signals: list[str]) -> list[Gene]:
        matches = []
        signal_set = set(s.lower() for s in signals)

        for gene in self._genes.values():
            gene_signals = set(s.lower() for s in gene.signals)
            overlap = signal_set & gene_signals
            if overlap:
                matches.append((gene, len(overlap)))

        matches.sort(key=lambda x: x[1], reverse=True)
        return [g for g, _ in matches]

    def get_gene(self, gene_id: str) -> Gene | None:
        return self._genes.get(gene_id)


class EvolutionEngine:
    """Evolution engine - manages gene evolution"""

    def __init__(self):
        self._matcher = GeneMatcher()
        self._capsules: dict[str, Capsule] = {}
        self._events: list[EvolutionEvent] = []

    def load_genes_from_dir(self, genes_dir: Path):
        if not genes_dir.exists():
            return

        for gene_file in genes_dir.glob("**/*.yaml"):
            try:
                data = yaml.safe_load(gene_file.read_text())
                if data.get("type") == "Gene":
                    gene = self._parse_gene(data)
                    self._matcher.register_gene(gene)
            except Exception:
                pass

    def _parse_gene(self, data: dict) -> Gene:
        return Gene(
            id=data.get("id", ""),
            version=data.get("version", "1.0.0"),
            category=GeneCategory(data.get("category", "repair")),
            signals=data.get("signals_match", []),
            preconditions=data.get("preconditions", []),
            strategy=data.get("strategy", []),
            constraints=data.get("constraints", {}),
            validation=data.get("validation", {}),
            metadata=data.get("metadata", {}),
            success_rate=data.get("metadata", {}).get("success_rate", 0.0),
            usage_count=data.get("metadata", {}).get("usage_count", 0),
        )

    def evolve(self, signals: list[str]) -> Gene | None:
        matches = self._matcher.match_signals(signals)
        if matches:
            gene = matches[0]
            gene.usage_count += 1
            self._record_event(EvolutionEventType.GENE_UPDATE, f"Selected gene: {gene.id}")
            return gene
        return None

    def create_capsule(self, trigger: list[str], gene: Gene, summary: str) -> Capsule:
        capsule = Capsule(
            id=f"capsule_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            trigger=trigger,
            gene_ref=gene.id,
            gene_version=gene.version,
            summary=summary,
        )
        self._capsules[capsule.id] = capsule
        self._record_event(EvolutionEventType.CAPSULE_CREATE, f"Created capsule: {capsule.id}")
        return capsule

    def _record_event(self, event_type: EvolutionEventType, description: str):
        event = EvolutionEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            description=description,
        )
        self._events.append(event)

    def get_events(self) -> list[EvolutionEvent]:
        return self._events.copy()

    def get_capsules(self) -> list[Capsule]:
        return list(self._capsules.values())

    def save(self, genes_path: str = None, capsules_path: str = None) -> None:
        """Save genes and capsules to files"""
        import json
        from pathlib import Path

        # Save genes
        if genes_path:
            genes_data = []
            for gene in self._matcher._genes.values():
                genes_data.append(
                    {
                        "id": gene.id,
                        "version": gene.version,
                        "category": gene.category.value
                        if hasattr(gene.category, "value")
                        else str(gene.category),
                        "signals": gene.signals,
                        "preconditions": gene.preconditions,
                        "strategy": gene.strategy,
                        "constraints": gene.constraints,
                        "validation": gene.validation,
                        "metadata": gene.metadata,
                        "success_rate": gene.success_rate,
                        "usage_count": gene.usage_count,
                    }
                )
            Path(genes_path).parent.mkdir(parents=True, exist_ok=True)
            with open(genes_path, "w", encoding="utf-8") as f:
                json.dump(genes_data, f, indent=2, ensure_ascii=False)

        # Save capsules
        if capsules_path:
            capsules_data = []
            for capsule in self._capsules.values():
                capsules_data.append(
                    {
                        "id": capsule.id,
                        "name": capsule.name,
                        "description": capsule.description,
                        "trigger": capsule.trigger,
                        "gene_ref": capsule.gene_ref,
                        "gene_version": capsule.gene_version,
                        "summary": capsule.summary,
                        "created_at": capsule.created_at.isoformat()
                        if capsule.created_at
                        else None,
                    }
                )
            Path(capsules_path).parent.mkdir(parents=True, exist_ok=True)
            with open(capsules_path, "w", encoding="utf-8") as f:
                json.dump(capsules_data, f, indent=2, ensure_ascii=False)

    def load(self, genes_path: str = None, capsules_path: str = None) -> None:
        """Load genes and capsules from files"""
        import json
        from pathlib import Path

        from src.evolver.models import Capsule, Gene, GeneCategory

        # Load genes
        if genes_path and Path(genes_path).exists():
            with open(genes_path, encoding="utf-8") as f:
                genes_data = json.load(f)
            for item in genes_data:
                category = item.get("category", "repair")
                if isinstance(category, str):
                    category = GeneCategory(category)
                gene = Gene(
                    id=item.get("id", ""),
                    version=item.get("version", "1.0.0"),
                    category=category,
                    signals=item.get("signals", []),
                    preconditions=item.get("preconditions", []),
                    strategy=item.get("strategy", []),
                    constraints=item.get("constraints", {}),
                    validation=item.get("validation", {}),
                    metadata=item.get("metadata", {}),
                    success_rate=item.get("success_rate", 0.0),
                    usage_count=item.get("usage_count", 0),
                )
                self._matcher.register_gene(gene)

        # Load capsules
        if capsules_path and Path(capsules_path).exists():
            with open(capsules_path, encoding="utf-8") as f:
                capsules_data = json.load(f)
            for item in capsules_data:
                capsule = Capsule(
                    id=item.get("id", ""),
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    trigger=item.get("trigger", []),
                    gene_ref=item.get("gene_ref", ""),
                    gene_version=item.get("gene_version", ""),
                    summary=item.get("summary", ""),
                    created_at=datetime.fromisoformat(item["created_at"])
                    if item.get("created_at")
                    else datetime.now(),
                )
                self._capsules[capsule.id] = capsule
        return list(self._capsules.values())


class PersonalityManager:
    """Personality manager - manages agent personality"""

    def __init__(self):
        self._personalities: dict[str, Personality] = {}

    def create_personality(self, name: str, traits: dict[str, float] = None) -> Personality:
        personality = Personality(name=name, traits=traits or {})
        self._personalities[name] = personality
        return personality

    def get_personality(self, name: str) -> Personality | None:
        return self._personalities.get(name)

    def update_trait(self, personality_name: str, trait: str, value: float) -> bool:
        personality = self._personalities.get(personality_name)
        if personality:
            personality.update_trait(trait, value)
            return True
        return False


def create_evolution_engine() -> EvolutionEngine:
    return EvolutionEngine()
