function R = rotationInterp(R0, R1, alpha)
%ROTATIONINTERP Interpolate between two rotation matrices.
% Uses matrix logarithm/exponential and re-orthonormalizes the result.

alpha = max(0, min(1, alpha));

if det(R0) < 0
    R0(:, 3) = -R0(:, 3);
end
if det(R1) < 0
    R1(:, 3) = -R1(:, 3);
end

Rrel = R0.' * R1;
A = real(logm(Rrel));
R = R0 * real(expm(alpha * A));

[U, ~, V] = svd(R);
R = U * V.';
if det(R) < 0
    U(:, 3) = -U(:, 3);
    R = U * V.';
end
end
