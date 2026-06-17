%% Parameter study for FDM print direction optimization
% This script studies how load and cantilever length change the recommended
% print direction and safety factor.

clear;
clc;
close all;

baseBeam.L = 0.100;
baseBeam.b = 0.020;
baseBeam.h = 0.010;

baseLoad.P = 50;
baseLoad.xP = baseBeam.L;
baseLoad.q = 0;

material.sigmaParallelAllow = 35e6;
material.sigmaPerpendicularAllow = 15e6;
material.tauLayerAllow = 8e6;
material.EParallel = 2.4e9;
material.EPerpendicular = 1.2e9;
material.G12 = 0.8e9;

design.nRequired = 2.0;
design.deflectionAllow = baseBeam.L / 100;
design.thetaMin = 0;
design.thetaMax = 90;
design.thetaStep = 5;

%% 1. Load study
loads = 20:10:100;
bestThetaLoad = zeros(size(loads));
bestSafetyLoad = zeros(size(loads));

for i = 1:numel(loads)
    beam = baseBeam;
    loadCase = baseLoad;
    loadCase.P = loads(i);
    loadCase.xP = beam.L;
    design.deflectionAllow = beam.L / 100;

    r = optimizePrintDirection(beam, loadCase, material, design);
    bestThetaLoad(i) = r.best.thetaDeg;
    bestSafetyLoad(i) = r.best.safetyFactor;
end

%% 2. Length study
lengths = 0.06:0.01:0.16;
bestThetaLength = zeros(size(lengths));
bestSafetyLength = zeros(size(lengths));

for i = 1:numel(lengths)
    beam = baseBeam;
    beam.L = lengths(i);
    loadCase = baseLoad;
    loadCase.xP = beam.L;
    design.deflectionAllow = beam.L / 100;

    r = optimizePrintDirection(beam, loadCase, material, design);
    bestThetaLength(i) = r.best.thetaDeg;
    bestSafetyLength(i) = r.best.safetyFactor;
end

%% 3. Plot
figure("Name", "FDM parameter study", "Color", "w");

subplot(2, 2, 1);
plot(loads, bestThetaLoad, "o-", "LineWidth", 1.5);
grid on;
xlabel("End force P (N)");
ylabel("Best theta (deg)");
title("Best print angle versus load");

subplot(2, 2, 2);
plot(loads, bestSafetyLoad, "s-", "LineWidth", 1.5);
grid on;
xlabel("End force P (N)");
ylabel("Best safety factor");
title("Safety factor versus load");

subplot(2, 2, 3);
plot(lengths * 1000, bestThetaLength, "o-", "LineWidth", 1.5);
grid on;
xlabel("Cantilever length L (mm)");
ylabel("Best theta (deg)");
title("Best print angle versus length");

subplot(2, 2, 4);
plot(lengths * 1000, bestSafetyLength, "s-", "LineWidth", 1.5);
grid on;
xlabel("Cantilever length L (mm)");
ylabel("Best safety factor");
title("Safety factor versus length");

fprintf("\nParameter study finished.\n");
