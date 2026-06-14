"""Process-bigraph Step wrapping the parsimony packing engine.

The Step takes per-ingredient counts as input (e.g. from an upstream whole-cell
model) and a structural *spec* as config (which structures/colors/categories,
the cell geometry, the chromosome), and emits a packed 3D cell.
"""
from __future__ import annotations
from process_bigraph import Step

from pbg_parsimony.api import Ingredient, Capsule, Chromosome, build_pack
from pbg_parsimony.structures import StructureRef


def _ref(d) -> StructureRef:
    return StructureRef(kind=d["kind"], ref=d["ref"])


def spec_to_ingredients(spec: dict, counts: dict | None = None) -> list[Ingredient]:
    """Build :class:`Ingredient` objects from a spec's ``ingredients`` list,
    overriding ``count`` from ``counts[id]`` when provided."""
    counts = counts or {}
    out = []
    for it in spec.get("ingredients", []):
        out.append(Ingredient(
            id=it["id"],
            count=int(counts.get(it["id"], it.get("count", 1))),
            structure=_ref(it["structure"]),
            color=tuple(it.get("color", (0.6, 0.6, 0.6))),
            region=it.get("region", "interior"),
            display_name=it.get("display_name", ""),
            category=it.get("category", ""),
            proxy_voxel_size=it.get("proxy_voxel_size"),
        ))
    return out


def spec_capsule(spec: dict) -> Capsule:
    cap = spec["capsule"]
    if "volume_fl" in cap:
        return Capsule.from_volume_fl(cap["volume_fl"], cap.get("radius_um", 0.5))
    return Capsule(half_len=cap["half_len"], radius=cap["radius"])


def spec_chromosome(spec: dict) -> Chromosome | None:
    c = spec.get("chromosome")
    if not c:
        return None
    seg = _ref(c["segment"]) if c.get("segment") else None
    kw = {k: c[k] for k in ("beads", "spacing", "bead_radius", "genome_csv", "supercoil")
          if k in c}
    return Chromosome(segment=seg, **kw)


class ParsimonyPackStep(Step):
    """Pack a 3D cell from molecular counts + a structural spec."""

    config_schema = {
        "spec": "any",
        "out_dir": {"_type": "string", "_default": "out/parsimony"},
        "name": {"_type": "string", "_default": "model"},
        "scale": {"_type": "float", "_default": 1.0},
        "proxy_lod": {"_type": "integer", "_default": 2},
    }

    def inputs(self):
        return {"counts": "any"}

    def outputs(self):
        return {"pack": "any"}

    def update(self, state, interval=None):
        spec = self.config["spec"]
        res = build_pack(
            spec_to_ingredients(spec, state.get("counts")),
            spec_capsule(spec),
            spec_chromosome(spec),
            out_dir=self.config["out_dir"], name=self.config["name"],
            scale=self.config["scale"], proxy_lod=self.config["proxy_lod"],
        )
        return {"pack": res}


def register_parsimony(core):
    """Register the Step so ``local:ParsimonyPackStep`` resolves in composites."""
    core.register_link("ParsimonyPackStep", ParsimonyPackStep)
    return core
