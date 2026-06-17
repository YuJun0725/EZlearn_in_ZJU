%% Run several 3D stress examples

clear;
clc;
close all;

unitName = "MPa";

examples = struct([]);

examples(1).name = "General 3D stress state";
examples(1).stress = makeStress(80, 40, -20, 30, 15, 25);

examples(2).name = "Plane stress with shear";
examples(2).stress = makeStress(100, 20, 0, 35, 0, 0);

examples(3).name = "Pure shear in xy plane";
examples(3).stress = makeStress(0, 0, 0, 50, 0, 0);

examples(4).name = "Hydrostatic tension";
examples(4).stress = makeStress(30, 30, 30, 0, 0, 0);

for i = 1:numel(examples)
    fprintf("\n========== %s ==========\n", examples(i).name);
    S = stressTensorFromComponents(examples(i).stress);
    result = calcPrincipalStress(S);
    printPrincipalResult(result, unitName);
    plotMohr3D(result, unitName);
end

function stress = makeStress(sx, sy, sz, txy, tyz, tzx)
stress.sigmaX = sx;
stress.sigmaY = sy;
stress.sigmaZ = sz;
stress.tauXY = txy;
stress.tauYZ = tyz;
stress.tauZX = tzx;
end
