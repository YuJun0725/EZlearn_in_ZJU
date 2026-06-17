function result = optimizePrintDirection(beam, loadCase, material, design)
%OPTIMIZEPRINTDIRECTION Enumerate print angles and select the best one.

arguments
    beam struct
    loadCase struct
    material struct
    design struct
end

thetaDeg = design.thetaMin:design.thetaStep:design.thetaMax;
if isempty(thetaDeg)
    error("optimizePrintDirection:EmptyAngles", "No candidate angle is generated.");
end

base = calcCantileverResponse(beam, loadCase, material.EParallel);

n = zeros(size(thetaDeg));
wMax = zeros(size(thetaDeg));
eEff = zeros(size(thetaDeg));
sigma1Top = zeros(size(thetaDeg));
sigma2Top = zeros(size(thetaDeg));
tau12Top = zeros(size(thetaDeg));
sigma1Bottom = zeros(size(thetaDeg));
sigma2Bottom = zeros(size(thetaDeg));
tau12Bottom = zeros(size(thetaDeg));
strengthOk = false(size(thetaDeg));
stiffnessOk = false(size(thetaDeg));

for i = 1:numel(thetaDeg)
    theta = deg2rad(thetaDeg(i));
    eEff(i) = equivalentBendingModulus(theta, material);
    angleResponse = calcCantileverResponse(beam, loadCase, eEff(i));
    wMax(i) = angleResponse.maxDeflection;

    topStress = transformPlaneStress(base.sigmaBending, 0, 0, theta);
    bottomStress = transformPlaneStress(-base.sigmaBending, 0, 0, theta);
    shearStress = transformPlaneStress(0, 0, base.tauShearMax, theta);

    sfTop = calcFdmSafetyFactor(topStress.sigma1, topStress.sigma2, topStress.tau12, material);
    sfBottom = calcFdmSafetyFactor(bottomStress.sigma1, bottomStress.sigma2, bottomStress.tau12, material);
    sfShear = calcFdmSafetyFactor(shearStress.sigma1, shearStress.sigma2, shearStress.tau12, material);

    n(i) = min([sfTop, sfBottom, sfShear]);

    sigma1Top(i) = topStress.sigma1;
    sigma2Top(i) = topStress.sigma2;
    tau12Top(i) = topStress.tau12;
    sigma1Bottom(i) = bottomStress.sigma1;
    sigma2Bottom(i) = bottomStress.sigma2;
    tau12Bottom(i) = bottomStress.tau12;

    strengthOk(i) = n(i) >= design.nRequired;
    stiffnessOk(i) = wMax(i) <= design.deflectionAllow;
end

feasible = strengthOk & stiffnessOk;
if any(feasible)
    feasibleIdx = find(feasible);
    [~, localBest] = max(n(feasibleIdx));
    bestIdx = feasibleIdx(localBest);
else
    [~, bestIdx] = max(n);
end

result = struct();
result.beam = beam;
result.loadCase = loadCase;
result.material = material;
result.base = base;
result.thetaDeg = thetaDeg;
result.safetyFactor = n;
result.maxDeflection = wMax;
result.effectiveModulus = eEff;
result.strengthOk = strengthOk;
result.stiffnessOk = stiffnessOk;
result.feasible = feasible;
result.sigma1Top = sigma1Top;
result.sigma2Top = sigma2Top;
result.tau12Top = tau12Top;
result.sigma1Bottom = sigma1Bottom;
result.sigma2Bottom = sigma2Bottom;
result.tau12Bottom = tau12Bottom;

result.best.index = bestIdx;
result.best.thetaDeg = thetaDeg(bestIdx);
result.best.safetyFactor = n(bestIdx);
result.best.maxDeflection = wMax(bestIdx);
result.best.effectiveModulus = eEff(bestIdx);
result.best.strengthOk = strengthOk(bestIdx);
result.best.stiffnessOk = stiffnessOk(bestIdx);
result.best.strengthStatus = statusText(strengthOk(bestIdx));
result.best.stiffnessStatus = statusText(stiffnessOk(bestIdx));
end

function text = statusText(ok)
if ok
    text = "OK";
else
    text = "NOT OK";
end
end
