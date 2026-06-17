# 3D Stress Principal Analysis and Animation

This Matlab project analyzes a general three-dimensional stress state.

It calculates:

- Principal stresses.
- Principal directions.
- Direction cosines and direction angles.
- Stress invariants.
- Maximum shear stress.
- Von Mises equivalent stress.
- Octahedral normal and shear stress.

It also visualizes:

- Original stress element.
- Stress element in principal directions.
- Principal stress axes.
- Three Mohr circles.
- Animation from original stress coordinates to principal stress coordinates.
- Mohr circle moving-point animation.

## First run

Open Matlab, enter this folder, and run:

```matlab
mainStress3D
```

The default example is:

```text
sigma_x = 80 MPa
sigma_y = 40 MPa
sigma_z = -20 MPa
tau_xy  = 30 MPa
tau_yz  = 15 MPa
tau_zx  = 25 MPa
```

You can edit these values at the top of `mainStress3D.m`.

## File list

| File | Role |
| --- | --- |
| `mainStress3D.m` | Main program |
| `stressTensorFromComponents.m` | Builds the stress tensor |
| `calcPrincipalStress.m` | Calculates principal stresses and directions |
| `printPrincipalResult.m` | Prints results in the command window |
| `plotStressCube.m` | Draws a stress element |
| `drawStressCube.m` | Low-level stress element drawing function |
| `plotPrincipalDirections.m` | Draws principal direction arrows |
| `plotMohr3D.m` | Draws three Mohr circles |
| `animatePrincipalRotation.m` | Animates rotation into principal coordinates |
| `animateMohrCircle.m` | Animates points on the Mohr circles |
| `rotationInterp.m` | Interpolates between two rotation matrices |
| `transformStressTensor.m` | Transforms stress tensor coordinates |
| `runStressExamples.m` | Runs several built-in verification examples |

## Notes

The program uses the sign convention that positive normal stress is tensile.
The stress tensor is stored as:

```text
S = [ sigma_x   tau_xy   tau_zx
      tau_xy    sigma_y  tau_yz
      tau_zx    tau_yz   sigma_z ]
```

The principal stresses are sorted as:

```text
sigma1 >= sigma2 >= sigma3
```

The principal directions are stored as column vectors in `result.V`.
