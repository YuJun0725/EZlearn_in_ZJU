%% 3D stress state principal stress analysis with animation
% Units in this example: MPa.

clear;
clc;
close all;

%% 1. Input stress components
stress.sigmaX = 80;
stress.sigmaY = 40;
stress.sigmaZ = -20;
stress.tauXY = 30;
stress.tauYZ = 15;
stress.tauZX = 25;

unitName = "MPa";

%% 2. Calculation
S = stressTensorFromComponents(stress);
result = calcPrincipalStress(S);

%% 3. Text output
printPrincipalResult(result, unitName);

%% 4. Static visualization
plotStressCube(S, "Original stress element", eye(3), unitName);
plotStressCube(diag(result.principalStresses), ...
    "Stress element in principal coordinates", result.V, unitName);
plotPrincipalDirections(result, unitName);
plotMohr3D(result, unitName);

%% 5. Animation settings
settings.playAnimations = true;
settings.frameCount = 80;
settings.pauseTime = 0.03;

if settings.playAnimations
    animatePrincipalRotation(S, result, settings.frameCount, settings.pauseTime, unitName);
    animateMohrCircle(result, settings.frameCount, settings.pauseTime, unitName);
end
