function result = calcPrincipalStress(S)
%CALCPRINCIPALSTRESS Calculate principal stresses and directions.

if ~isequal(size(S), [3, 3])
    error("calcPrincipalStress:InvalidSize", "Stress tensor must be 3 by 3.");
end

S = 0.5 * (S + S.');

[V, D] = eig(S);
principal = diag(D);
[principal, order] = sort(principal, "descend");
V = V(:, order);

% Make the direction matrix right-handed for smooth visualization.
if det(V) < 0
    V(:, 3) = -V(:, 3);
end

SPrincipal = V.' * S * V;
SPrincipal = 0.5 * (SPrincipal + SPrincipal.');

s1 = principal(1);
s2 = principal(2);
s3 = principal(3);

I1 = trace(S);
I2 = 0.5 * (trace(S)^2 - trace(S * S));
I3 = det(S);

tauMax = (s1 - s3) / 2;
meanStress = I1 / 3;
vonMises = sqrt(0.5 * ((s1 - s2)^2 + (s2 - s3)^2 + (s3 - s1)^2));
octNormal = meanStress;
octShear = (1 / 3) * sqrt((s1 - s2)^2 + (s2 - s3)^2 + (s3 - s1)^2);

directionCosines = V;
directionAngles = acosd(max(min(directionCosines, 1), -1));

result = struct();
result.S = S;
result.V = V;
result.D = diag(principal);
result.principalStresses = principal;
result.SPrincipal = SPrincipal;
result.directionCosines = directionCosines;
result.directionAngles = directionAngles;
result.I1 = I1;
result.I2 = I2;
result.I3 = I3;
result.tauMax = tauMax;
result.meanStress = meanStress;
result.vonMises = vonMises;
result.octNormal = octNormal;
result.octShear = octShear;
end
