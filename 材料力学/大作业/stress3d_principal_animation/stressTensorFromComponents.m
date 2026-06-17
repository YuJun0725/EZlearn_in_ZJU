function S = stressTensorFromComponents(stress)
%STRESSTENSORFROMCOMPONENTS Build a symmetric 3D stress tensor.

S = [stress.sigmaX, stress.tauXY, stress.tauZX; ...
     stress.tauXY, stress.sigmaY, stress.tauYZ; ...
     stress.tauZX, stress.tauYZ, stress.sigmaZ];

S = 0.5 * (S + S.');
end
