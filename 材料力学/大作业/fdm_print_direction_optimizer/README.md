# FDM Print Direction Optimizer

This Matlab program studies how the print raster direction affects the
strength of an FDM printed cantilever bracket or hook.

The structure is simplified as a rectangular cantilever beam:

- Left end fixed.
- Right end loaded by a vertical concentrated force.
- Optional uniform load can represent self weight or distributed service load.
- The critical section is usually near the fixed end.

The program enumerates candidate print directions and evaluates:

- Maximum bending stress.
- Maximum transverse shear stress.
- Stress components in the local print material coordinates.
- Strength safety factor.
- Effective bending modulus.
- Maximum deflection.

## Main files

| File | Role |
| --- | --- |
| `mainFdmPrintDirection.m` | Main example program |
| `optimizePrintDirection.m` | Enumerates print angles and selects the best one |
| `calcCantileverResponse.m` | Calculates cantilever reaction, internal force, stress, and deflection |
| `transformPlaneStress.m` | Transforms stress from beam coordinates to print material coordinates |
| `calcFdmSafetyFactor.m` | Calculates safety factor under anisotropic FDM allowables |
| `equivalentBendingModulus.m` | Estimates angle-dependent effective modulus |
| `plotOptimizationResult.m` | Plots safety factor, deflection, and angle recommendation |
| `runParameterStudy.m` | Studies the effect of beam length and load |

## Suggested first run

Open Matlab, enter this folder, and run:

```matlab
mainFdmPrintDirection
```

Then run:

```matlab
runParameterStudy
```

## Model parameters

Geometry:

```text
L  cantilever length
b  rectangular section width
h  rectangular section height
```

Loads:

```text
P  vertical concentrated force at xP
q  optional uniform distributed load
```

FDM strength:

```text
sigmaParallelAllow       allowable normal stress along raster direction
sigmaPerpendicularAllow  allowable normal stress transverse to raster direction
tauLayerAllow            allowable shear stress in print material coordinate
```

Print direction:

```text
theta = angle from beam axis x to print raster direction
```

## Important assumptions

This is a material-mechanics design model, not a full finite-element model.
It is suitable for a course project because it connects beam bending theory
with anisotropic FDM material behavior.

For a real printed part, actual strength also depends on nozzle temperature,
layer height, infill ratio, wall count, material, cooling, defects, and local
stress concentration near screw holes or fillets.
