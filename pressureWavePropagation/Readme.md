# Pressure Wave Propagation Case

This directory contains an OpenFOAM setup for a two-dimensional pressure wave propagation test. The case uses a small oscillating pressure patch inside a rectangular domain to generate acoustic waves in otherwise quiescent air. The resulting pressure field can be post-processed with `animate_waves.py` to create an animation of the normalized pressure fluctuation.

## Physical Setup

The computational domain is a thin 2D box with empty front and back boundaries:

- `x = 0 ... 300`
- `y = 0 ... 300`
- `z = 0 ... 0.05`

The pressure source is located near the center of the domain at approximately `(x, y) = (100, 150)`. It is represented by a small patch spanning:

- `x = 99.5 ... 100.5`
- `y = 149.5 ... 150.5`

The initial state is uniform air at rest:

- `p0 = 101325 Pa`
- `T0 = 300 K`
- `U0 = (0 0 0) m/s`

The `pressureSource` patch imposes a sinusoidal pressure signal with:

- frequency: `100 Hz`
- amplitude: `1013.25 Pa`, i.e. `1%` of `p0`
- offset level: `101325 Pa`

## Mesh

The mesh is generated with `blockMesh`. It consists of nine structured hexahedral blocks arranged around the pressure source patch. The domain is one cell thick in the `z` direction and uses `empty` front/back patches for a 2D calculation.

## Solver and Numerics

The solver is selected in `system/controlDict`:

```text
application rhoPimpleFoam;
```

Main time controls:

- start from latest available time
- end time: `0.25 s`
- time step: `5e-5 s`
- write interval: `1e-3 s`
- binary result writing
- fixed time step, `adjustTimeStep false`
- target Courant setting retained as `maxCo 0.3`

## Running the Case

From the case directory:

```bash
cd pressureWavePropagation
./Allrun
```

`Allrun` performs the following steps:

1. Copies `0.orig` to `0`.
2. Creates `post.foam` for ParaView loading.
3. Runs `blockMesh`.
4. Decomposes the case with `decomposePar`.
5. Runs `checkMesh` in parallel.
6. Renumbers the mesh in parallel.
7. Runs `rhoPimpleFoam` in parallel.
8. Writes cell centers and cell volumes with `postProcess`.

To clean the case:

```bash
./Allclean
```

## Postprocessing

To animate the fields run the `animate_waves.py`, make sure to set the correct `load_path` and `save_path` first.