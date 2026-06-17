function response = calcCantileverResponse(beam, loadCase, E)
%CALCCANTILEVERRESPONSE Calculate cantilever stress and deflection.
% Downward load magnitude is treated as positive for simple design output.

arguments
    beam struct
    loadCase struct
    E (1,1) double {mustBePositive}
end

L = beam.L;
b = beam.b;
h = beam.h;
P = getFieldOr(loadCase, "P", 0);
xP = getFieldOr(loadCase, "xP", L);
q = getFieldOr(loadCase, "q", 0);

if L <= 0 || b <= 0 || h <= 0
    error("calcCantileverResponse:InvalidGeometry", "L, b, and h must be positive.");
end
if xP < 0 || xP > L
    error("calcCantileverResponse:InvalidLoadPosition", "xP must be within [0, L].");
end

A = b * h;
I = b * h^3 / 12;
yMax = h / 2;

% Fixed-end moment for a point force at xP and uniform load on [0, L].
Mmax = P * xP + q * L^2 / 2;
Vfixed = P + q * L;

sigmaBending = Mmax * yMax / I;

% Maximum shear stress for a rectangular section.
tauShearMax = 1.5 * abs(Vfixed) / A;

% Deflection at the free end.
% A point force located at xP causes no curvature over x > xP, but the free
% end still moves by the tangent generated over [0, xP].
wPoint = P * xP^2 * (3 * L - xP) / (6 * E * I);
if xP == 0
    wPoint = 0;
end
wUniform = q * L^4 / (8 * E * I);
wMax = abs(wPoint + wUniform);

response = struct();
response.A = A;
response.I = I;
response.yMax = yMax;
response.reactionForce = Vfixed;
response.reactionMoment = Mmax;
response.criticalX = 0;
response.maxMoment = Mmax;
response.sigmaBending = abs(sigmaBending);
response.tauShearMax = tauShearMax;
response.maxDeflection = wMax;
end

function value = getFieldOr(s, name, defaultValue)
if isfield(s, name)
    value = s.(name);
else
    value = defaultValue;
end
end
