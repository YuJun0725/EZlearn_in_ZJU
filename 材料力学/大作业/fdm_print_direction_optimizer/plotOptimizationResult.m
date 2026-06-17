function plotOptimizationResult(result, design)
%PLOTOPTIMIZATIONRESULT Plot optimization curves.

arguments
    result struct
    design struct
end

theta = result.thetaDeg;

figure("Name", "FDM print direction optimization", "Color", "w");

subplot(3, 1, 1);
plot(theta, result.safetyFactor, "o-", "LineWidth", 1.5);
hold on;
yline(design.nRequired, "--r", "Required n");
xline(result.best.thetaDeg, "--k", "Best");
grid on;
xlabel("Print angle theta (deg)");
ylabel("Safety factor");
title("Strength safety factor versus print direction");

subplot(3, 1, 2);
plot(theta, result.maxDeflection * 1000, "s-", "LineWidth", 1.5);
hold on;
yline(design.deflectionAllow * 1000, "--r", "Allowable");
xline(result.best.thetaDeg, "--k", "Best");
grid on;
xlabel("Print angle theta (deg)");
ylabel("Max deflection (mm)");
title("Deflection versus print direction");

subplot(3, 1, 3);
plot(theta, result.effectiveModulus / 1e9, "^-", "LineWidth", 1.5);
hold on;
xline(result.best.thetaDeg, "--k", "Best");
grid on;
xlabel("Print angle theta (deg)");
ylabel("Effective E (GPa)");
title("Estimated effective bending modulus");

figure("Name", "Local stress components at critical section", "Color", "w");
plot(theta, result.sigma1Top / 1e6, "o-", "LineWidth", 1.5);
hold on;
plot(theta, result.sigma2Top / 1e6, "s-", "LineWidth", 1.5);
plot(theta, result.tau12Top / 1e6, "^-", "LineWidth", 1.5);
xline(result.best.thetaDeg, "--k", "Best");
grid on;
xlabel("Print angle theta (deg)");
ylabel("Stress (MPa)");
legend("sigma1 top", "sigma2 top", "tau12 top", "Location", "best");
title("Transformed stress components on tensile outer fiber");
end
