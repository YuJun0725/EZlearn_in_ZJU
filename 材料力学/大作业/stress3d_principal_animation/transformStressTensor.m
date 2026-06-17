function SLocal = transformStressTensor(S, R)
%TRANSFORMSTRESSTENSOR Transform stress tensor into axes stored in R.
% Columns of R are the local axes written in global coordinates.

SLocal = R.' * S * R;
SLocal = 0.5 * (SLocal + SLocal.');
end
