function printPrincipalResult(result, unitName)
%PRINTPRINCIPALRESULT Print principal stress calculation results.

if nargin < 2
    unitName = "";
end

s = result.principalStresses;

fprintf("\n3D stress state principal stress analysis\n");
fprintf("--------------------------------------------------\n");
fprintf("Stress tensor S (%s):\n", unitName);
disp(result.S);

fprintf("Principal stresses (%s):\n", unitName);
fprintf("sigma1 = %.6g\n", s(1));
fprintf("sigma2 = %.6g\n", s(2));
fprintf("sigma3 = %.6g\n", s(3));

fprintf("\nPrincipal direction cosines, columns are n1, n2, n3:\n");
disp(result.directionCosines);

fprintf("Principal direction angles with x, y, z axes (deg):\n");
disp(result.directionAngles);

fprintf("Stress invariants:\n");
fprintf("I1 = %.6g\n", result.I1);
fprintf("I2 = %.6g\n", result.I2);
fprintf("I3 = %.6g\n", result.I3);

fprintf("\nDerived quantities (%s):\n", unitName);
fprintf("Maximum shear stress tau_max = %.6g\n", result.tauMax);
fprintf("Mean stress sigma_m = %.6g\n", result.meanStress);
fprintf("Von Mises equivalent stress = %.6g\n", result.vonMises);
fprintf("Octahedral normal stress = %.6g\n", result.octNormal);
fprintf("Octahedral shear stress = %.6g\n", result.octShear);
fprintf("--------------------------------------------------\n\n");
end
