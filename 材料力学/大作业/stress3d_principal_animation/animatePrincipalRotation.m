function animatePrincipalRotation(S, result, frameCount, pauseTime, unitName)
%ANIMATEPRINCIPALROTATION Animate rotation from original to principal axes.

if nargin < 3
    frameCount = 80;
end
if nargin < 4
    pauseTime = 0.03;
end
if nargin < 5
    unitName = "";
end

figure("Name", "Animation: rotation to principal directions", "Color", "w");
ax = axes;

for k = 1:frameCount
    a = (k - 1) / max(frameCount - 1, 1);
    R = rotationInterp(eye(3), result.V, a);
    SLocal = transformStressTensor(S, R);

    drawStressCube(ax, SLocal, ...
        sprintf("Rotation to principal directions, %.0f%%", 100 * a), ...
        R, unitName);

    drawnow;
    pause(pauseTime);
end
end
