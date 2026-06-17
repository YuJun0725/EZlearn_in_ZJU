function n = calcFdmSafetyFactor(sigma1, sigma2, tau12, material)
%CALCFDMSAFETYFACTOR Maximum-stress safety factor for FDM anisotropy.

arguments
    sigma1 (1,1) double
    sigma2 (1,1) double
    tau12 (1,1) double
    material struct
end

allow1 = material.sigmaParallelAllow;
allow2 = material.sigmaPerpendicularAllow;
allow12 = material.tauLayerAllow;

if allow1 <= 0 || allow2 <= 0 || allow12 <= 0
    error("calcFdmSafetyFactor:InvalidAllowable", "Material allowables must be positive.");
end

util1 = abs(sigma1) / allow1;
util2 = abs(sigma2) / allow2;
util12 = abs(tau12) / allow12;
util = max([util1, util2, util12]);

if util == 0
    n = inf;
else
    n = 1 / util;
end
end
