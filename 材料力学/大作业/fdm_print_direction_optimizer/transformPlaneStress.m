function localStress = transformPlaneStress(sigmaX, sigmaY, tauXY, theta)
%TRANSFORMPLANESTRESS Transform plane stress to local print coordinates.
% theta is the angle from global x to local 1 direction.

arguments
    sigmaX (1,1) double
    sigmaY (1,1) double
    tauXY (1,1) double
    theta (1,1) double
end

c = cos(theta);
s = sin(theta);

sigma1 = sigmaX * c^2 + sigmaY * s^2 + 2 * tauXY * s * c;
sigma2 = sigmaX * s^2 + sigmaY * c^2 - 2 * tauXY * s * c;
tau12 = (sigmaY - sigmaX) * s * c + tauXY * (c^2 - s^2);

localStress = struct();
localStress.sigma1 = sigma1;
localStress.sigma2 = sigma2;
localStress.tau12 = tau12;
end
