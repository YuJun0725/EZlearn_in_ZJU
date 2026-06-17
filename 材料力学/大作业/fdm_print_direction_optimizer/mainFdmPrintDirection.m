%% FDM print direction optimization for a cantilever bracket
% This script is the main entry point.
% Units: m, N, Pa.

clear;
clc;
close all;

%% 1. Geometry and load
beam.L = 0.100;          % Cantilever length, m
beam.b = 0.020;          % Rectangular section width, m
beam.h = 0.010;          % Rectangular section height, m

loadCase.P = 50;         % Downward end force magnitude, N
loadCase.xP = beam.L;    % Force position, m
loadCase.q = 0;          % Uniform load magnitude, N/m, downward positive

%% 2. FDM material allowables
% Example values for a generic printed plastic. Replace them with measured
% values if tensile tests are available.
material.sigmaParallelAllow = 35e6;       % Pa
material.sigmaPerpendicularAllow = 15e6;  % Pa
material.tauLayerAllow = 8e6;             % Pa

% Moduli used for deflection comparison.
material.EParallel = 2.4e9;       % Pa
material.EPerpendicular = 1.2e9;  % Pa
material.G12 = 0.8e9;             % Pa

%% 3. Design requirements and search range
design.nRequired = 2.0;
design.deflectionAllow = beam.L / 100;
design.thetaMin = 0;
design.thetaMax = 90;
design.thetaStep = 5;

%% 4. Solve
result = optimizePrintDirection(beam, loadCase, material, design);

%% 5. Print summary
fprintf("\nFDM print direction optimization finished.\n");
fprintf("Best print angle theta = %.1f deg\n", result.best.thetaDeg);
fprintf("Best safety factor n = %.3f\n", result.best.safetyFactor);
fprintf("Maximum deflection at best angle = %.6g m\n", result.best.maxDeflection);
fprintf("Allowable deflection = %.6g m\n", design.deflectionAllow);
fprintf("Strength status: %s\n", result.best.strengthStatus);
fprintf("Stiffness status: %s\n", result.best.stiffnessStatus);

fprintf("\nCritical section x = %.6g m\n", result.base.criticalX);
fprintf("Maximum bending moment = %.6g N*m\n", result.base.maxMoment);
fprintf("Maximum beam-axis bending stress = %.6g Pa\n", result.base.sigmaBending);
fprintf("Maximum rectangular-section shear stress = %.6g Pa\n", result.base.tauShearMax);

%% 6. Plot
plotOptimizationResult(result, design);
