"""High-level API: turn an ingredient list + cell geometry into a 3D pack.

This is the reusable core of pbg-parsimony. Organism-specific logic (which
molecules, their names/categories/abundances) lives in the caller (e.g.
v2ecoli); pbg-parsimony resolves structures, authors the recipe, and runs the
parsimony engine.
"""
from __future__ import annotations
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from pbg_parsimony.structures import StructureRef, fetch
from pbg_parsimony.engine import mesh_file, run_pipeline
from pbg_parsimony.recipe import object_block, author_recipe, build_pipeline


@dataclass
class Ingredient:
    """One molecular species to place. ``id`` is the unique key (becomes the
    recipe object key and the pack ingredient ``name``); ``region`` is
    ``interior`` | ``surface`` | ``fiber``.

    Provide a ``structure`` (meshed to a VdW surface) OR a ``sphere_radius``
    (a cheap sphere proxy, e.g. for membrane lipids). ``principal_vector``
    orients surface ingredients to the membrane normal."""
    id: str
    count: int
    structure: StructureRef | None = None
    sphere_radius: float | None = None
    color: tuple = (0.6, 0.6, 0.6)
    region: str = "interior"
    display_name: str = ""
    category: str = ""
    proxy_voxel_size: float | None = None
    principal_vector: tuple | None = None
    lod_count: int = 4


@dataclass
class Capsule:
    """Spherocylinder cell geometry in Ångström (medial half-length + cap radius)."""
    half_len: float
    radius: float

    @classmethod
    def from_volume_fl(cls, volume_fl: float, radius_um: float = 0.5) -> "Capsule":
        """Capsule sized to a cell volume (fL≈µm³): V = πr²L + (4/3)πr³."""
        import math
        r = radius_um * 1e4  # µm → Å
        v = volume_fl * 1e12  # µm³ → Å³
        lcyl = max(0.0, (v - (4.0 / 3.0) * math.pi * r ** 3) / (math.pi * r ** 2))
        return cls(half_len=max(r, lcyl / 2.0), radius=r)


@dataclass
class Chromosome:
    """A supercoiled rod nucleoid. ``segment`` is the dsDNA mesh (e.g. RCSB
    1BNA); ``proteins`` are ingredient ids to bind along the fiber."""
    beads: int = 34000
    spacing: float = 135.0
    bead_radius: float = 12.0
    genome_csv: str | None = None
    supercoil: dict = field(default_factory=lambda: {"radius": 90.0, "pitch": 130.0, "domains": 200})
    segment: StructureRef | None = None
    segment_id: str = "dna_segment"
    color: tuple = (0.85, 0.75, 0.45)
    proteins: list = field(default_factory=list)


def build_pack(ingredients, capsule: Capsule, chromosome: Chromosome | None = None, *,
               out_dir, name: str = "model", scale: float = 1.0, proxy_lod: int = 2) -> dict:
    """Resolve + mesh structures, author the recipe, and pack the cell.

    Returns ``{pack_path, sidecar_path, recipe_path, pipeline_path, n_placed,
    ingredients}``. Meshes go in ``<out_dir>/meshes``; structures cache in
    ``<out_dir>/structures``; the recipe references meshes as ``meshes/…``.
    """
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    struct_cache = out_dir / "structures"
    mesh_dir = out_dir / "meshes"
    objects, interior, surface, fiber, sidecar = {}, [], [], [], {}
    surface_ids = []

    def add_mesh(obj_id, ref, color, proxy=None, lod_count=4):
        path = fetch(ref, struct_cache, slug=obj_id)
        stem = mesh_file(path, mesh_dir)
        lods = [f"meshes/{stem}.lod{i}.obj" for i in range(lod_count)
                if (mesh_dir / f"{stem}.lod{i}.obj").exists()]
        if not lods:
            return False
        objects[obj_id] = object_block(color, lods, proxy)
        return True

    for ing in ingredients:
        if ing.structure is None and ing.sphere_radius is not None:
            obj = {"type": "single_sphere", "radius": float(ing.sphere_radius),
                   "color": [float(c) for c in ing.color]}
            if ing.principal_vector is not None:
                obj["principal_vector"] = list(ing.principal_vector)
            objects[ing.id] = obj
        else:
            try:
                if not add_mesh(ing.id, ing.structure, ing.color, ing.proxy_voxel_size, ing.lod_count):
                    print(f"  skip {ing.id}: no LODs"); continue
            except Exception as e:  # noqa: BLE001 — one bad structure shouldn't kill the build
                print(f"  skip {ing.id}: structure error {str(e)[:60]}"); continue
        cnt = max(1, int(ing.count * scale))
        sidecar[ing.id] = {"display_name": ing.display_name or ing.id,
                           "category": ing.category, "count": cnt}
        directive = {"object": ing.id, "count": cnt}
        if ing.region == "surface":
            surface.append(directive); surface_ids.append(ing.id)
        elif ing.region == "fiber":
            fiber.append(directive)
        else:
            interior.append(directive)

    chrom_block = None
    if chromosome is not None:
        if chromosome.segment is not None:
            add_mesh(chromosome.segment_id, chromosome.segment, chromosome.color)
        genome_rel = None
        if chromosome.genome_csv:
            shutil.copy(chromosome.genome_csv, out_dir / "genome.csv")
            genome_rel = "genome.csv"
        chrom_block = {
            "beads": chromosome.beads, "spacing": chromosome.spacing,
            "bead_radius": chromosome.bead_radius, "color": list(chromosome.color),
            "compartment": "cell", "segment": chromosome.segment_id,
            "supercoil": chromosome.supercoil, "proteins": fiber,
        }
        if genome_rel:
            chrom_block["genome"] = genome_rel
        sidecar[chromosome.segment_id] = {
            "display_name": "Chromosomal DNA (B-form duplex)",
            "category": "Nucleoid", "count": chromosome.beads}

    recipe = author_recipe(name, objects, interior, surface,
                           {"half_len": capsule.half_len, "radius": capsule.radius}, chrom_block)
    recipe_path = out_dir / f"{name}.json"
    recipe_path.write_text(json.dumps(recipe, indent=2))
    pipeline = build_pipeline(name, f"{name}.json", surface_ids=surface_ids,
                              has_chromosome=chrom_block is not None,
                              has_fiber_proteins=bool(fiber))
    pipeline_path = out_dir / f"{name}.pipeline.json"
    pipeline_path.write_text(json.dumps(pipeline, indent=2))
    sidecar_path = out_dir / f"{name}.meta.json"
    sidecar_path.write_text(json.dumps({"ingredients": sidecar}, indent=1))

    pack_path = out_dir / f"{name}.pack.json"
    res = run_pipeline(pipeline_path, pack_path, proxy_lod=proxy_lod)
    n_placed = 0
    try:
        n_placed = len(json.loads(pack_path.read_text()).get("placements", []))
    except Exception:
        pass
    return {"pack_path": str(pack_path), "sidecar_path": str(sidecar_path),
            "recipe_path": str(recipe_path), "pipeline_path": str(pipeline_path),
            "n_placed": n_placed, "ingredients": len(sidecar), "stdout": res["stdout"]}
