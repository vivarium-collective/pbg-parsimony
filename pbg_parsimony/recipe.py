"""Author parsimony recipe + staged-pipeline JSON from resolved ingredients."""
from __future__ import annotations

LOD_VOXELS = [16.0, 8.0, 4.0, 2.5]


def object_block(color, lod_paths, proxy_voxel_size=None):
    """A mesh ingredient object for the recipe ``objects`` map."""
    o = {
        "type": "mesh",
        "color": [float(c) for c in color],
        "mesh_lods": [{"path": p, "voxel_size": LOD_VOXELS[min(i, len(LOD_VOXELS) - 1)]}
                      for i, p in enumerate(lod_paths)],
    }
    if proxy_voxel_size:
        o["proxy_voxel_size"] = float(proxy_voxel_size)
    return o


def author_recipe(name, objects, interior, surface, capsule, chromosome=None, bbox_pad=1.2):
    """Assemble a ``2.1-parsimony`` recipe dict. ``capsule`` is
    ``{"half_len","radius"}`` (Å); ``chromosome`` is a recipe chromosome block."""
    half, r = float(capsule["half_len"]), float(capsule["radius"])
    recipe = {
        "name": name, "version": "0.1.0", "format_version": "2.1-parsimony",
        "description": "Packed by pbg-parsimony.",
        "bounding_box": [[-(half + r), -r * bbox_pad, -r * bbox_pad],
                         [half + r, r * bbox_pad, r * bbox_pad]],
        "objects": objects,
        "composition": {
            "space": {"regions": {"interior": ["cell"]}},
            "cell": {
                "compartment": {"kind": "capsule", "a": [-half, 0, 0], "b": [half, 0, 0], "radius": r},
                "regions": {"interior": interior, "surface": surface},
            },
        },
    }
    if chromosome:
        recipe["chromosome"] = chromosome
    return recipe


def build_pipeline(name, recipe_rel, *, surface_ids, has_chromosome, has_fiber_proteins,
                   backend="octree", clearance_cell_size=40):
    """Staged octree pipeline: chromosome → membrane (surface) → fiber proteins →
    densified interior."""
    stages = []
    deps_for_interior = []
    if has_chromosome:
        stages.append({"id": "chromosome", "kind": "chromosome"})
        deps_for_interior.append("chromosome")
    if surface_ids:
        stages.append({"id": "membrane", "kind": "pack",
                       "include": list(surface_ids), "exclude": [], "densify": False})
    if has_chromosome and has_fiber_proteins:
        stages.append({"id": "fiber_proteins", "kind": "fiber_pack", "depends_on": ["chromosome"]})
        deps_for_interior.append("fiber_proteins")
    interior_stage = {"id": "interior", "kind": "pack", "include": [],
                      "exclude": list(surface_ids), "densify": True,
                      "clearance_cell_size": clearance_cell_size}
    if deps_for_interior:
        interior_stage["depends_on"] = deps_for_interior
    stages.append(interior_stage)
    return {"name": name, "recipe": recipe_rel, "seed": 0,
            "strict_bounds": True, "backend": backend, "stages": stages}
