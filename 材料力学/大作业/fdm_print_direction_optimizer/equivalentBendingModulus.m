function eEff = equivalentBendingModulus(theta, material)
%EQUIVALENTBENDINGMODULUS Estimate angle-dependent modulus.
% This uses the transformed compliance expression for an orthotropic lamina:
% 1/E(theta) = c^4/E1 + s^4/E2 + (1/G12 - 2*nu12/E1)*s^2*c^2.
% nu12 is optional and defaults to 0.30.

arguments
    theta (1,1) double
    material struct
end

E1 = material.EParallel;
E2 = material.EPerpendicular;
G12 = material.G12;
nu12 = getFieldOr(material, "nu12", 0.30);

if E1 <= 0 || E2 <= 0 || G12 <= 0
    error("equivalentBendingModulus:InvalidModulus", "EParallel, EPerpendicular, and G12 must be positive.");
end

c = cos(theta);
s = sin(theta);

compliance = c^4 / E1 + s^4 / E2 + (1 / G12 - 2 * nu12 / E1) * s^2 * c^2;
if compliance <= 0
    eEff = min(E1, E2);
else
    eEff = 1 / compliance;
end
end

function value = getFieldOr(s, name, defaultValue)
if isfield(s, name)
    value = s.(name);
else
    value = defaultValue;
end
end
