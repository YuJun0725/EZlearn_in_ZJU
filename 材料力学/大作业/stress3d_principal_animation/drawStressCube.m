function drawStressCube(ax, S, titleText, R, unitName)
%DRAWSTRESSCUBE Draw a cube and traction vectors on its faces.
% S is expressed in the local cube coordinates.
% R maps local cube coordinates to global drawing coordinates.

if nargin < 4
    R = eye(3);
end
if nargin < 5
    unitName = "";
end

cla(ax);
hold(ax, "on");
grid(ax, "on");
axis(ax, "equal");
view(ax, 35, 25);

verticesLocal = 0.5 * [ ...
    -1 -1 -1;
     1 -1 -1;
     1  1 -1;
    -1  1 -1;
    -1 -1  1;
     1 -1  1;
     1  1  1;
    -1  1  1];

verticesGlobal = (R * verticesLocal.').';
faces = [1 2 3 4; 5 6 7 8; 1 2 6 5; 2 3 7 6; 3 4 8 7; 4 1 5 8];

patch(ax, "Vertices", verticesGlobal, "Faces", faces, ...
    "FaceColor", [0.75 0.85 1.00], "FaceAlpha", 0.16, ...
    "EdgeColor", [0.1 0.1 0.1], "LineWidth", 1.0);

maxStress = max(abs(S), [], "all");
if maxStress == 0
    maxStress = 1;
end
arrowScale = 0.42 / maxStress;

normals = [ ...
     1  0  0;
    -1  0  0;
     0  1  0;
     0 -1  0;
     0  0  1;
     0  0 -1];

for i = 1:size(normals, 1)
    nLocal = normals(i, :).';
    centerLocal = 0.55 * nLocal;
    tractionLocal = S * nLocal;

    centerGlobal = R * centerLocal;
    tractionGlobal = R * tractionLocal * arrowScale;

    color = tractionColor(tractionLocal, nLocal);
    quiver3(ax, centerGlobal(1), centerGlobal(2), centerGlobal(3), ...
        tractionGlobal(1), tractionGlobal(2), tractionGlobal(3), ...
        0, "LineWidth", 2.0, "Color", color, "MaxHeadSize", 0.8);
end

drawBasis(ax, R);

offDiag = S - diag(diag(S));
maxShearComponent = max(abs(offDiag), [], "all");

xlabel(ax, "x");
ylabel(ax, "y");
zlabel(ax, "z");
title(ax, sprintf("%s\nmax off-diagonal shear component = %.4g %s", ...
    titleText, maxShearComponent, unitName), "Interpreter", "none");

limit = 1.25;
xlim(ax, [-limit, limit]);
ylim(ax, [-limit, limit]);
zlim(ax, [-limit, limit]);
hold(ax, "off");
end

function drawBasis(ax, R)
labels = ["x'", "y'", "z'"];
colors = [0.85 0.1 0.1; 0.1 0.55 0.1; 0.1 0.2 0.85];
for i = 1:3
    v = R(:, i);
    quiver3(ax, 0, 0, 0, v(1), v(2), v(3), ...
        0.75, "LineWidth", 1.6, "Color", colors(i, :), "MaxHeadSize", 0.6);
    text(ax, 0.82 * v(1), 0.82 * v(2), 0.82 * v(3), labels(i), ...
        "Color", colors(i, :), "FontWeight", "bold");
end
end

function color = tractionColor(tractionLocal, normalLocal)
normalPart = dot(tractionLocal, normalLocal);
shearPart = norm(tractionLocal - normalPart * normalLocal);
if abs(normalPart) >= shearPart
    if normalPart >= 0
        color = [0.80 0.05 0.05];
    else
        color = [0.05 0.20 0.85];
    end
else
    color = [0.85 0.45 0.05];
end
end
