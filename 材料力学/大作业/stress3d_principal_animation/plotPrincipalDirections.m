function plotPrincipalDirections(result, unitName)
%PLOTPRINCIPALDIRECTIONS Plot principal directions as 3D arrows.

if nargin < 2
    unitName = "";
end

figure("Name", "Principal directions", "Color", "w");
ax = axes;
hold(ax, "on");
grid(ax, "on");
axis(ax, "equal");
view(ax, 35, 25);

colors = [0.85 0.1 0.1; 0.1 0.55 0.1; 0.1 0.2 0.85];
labels = ["sigma1", "sigma2", "sigma3"];

for i = 1:3
    v = result.V(:, i);
    quiver3(ax, 0, 0, 0, v(1), v(2), v(3), ...
        0.95, "LineWidth", 2.4, "Color", colors(i, :), "MaxHeadSize", 0.6);
    quiver3(ax, 0, 0, 0, -v(1), -v(2), -v(3), ...
        0.95, "LineWidth", 1.0, "Color", colors(i, :), "MaxHeadSize", 0.4);
    text(ax, 1.05 * v(1), 1.05 * v(2), 1.05 * v(3), ...
        sprintf("%s = %.4g %s", labels(i), result.principalStresses(i), unitName), ...
        "Color", colors(i, :), "FontWeight", "bold");
end

quiver3(ax, 0, 0, 0, 1, 0, 0, 0.55, "k", "LineStyle", "--");
quiver3(ax, 0, 0, 0, 0, 1, 0, 0.55, "k", "LineStyle", "--");
quiver3(ax, 0, 0, 0, 0, 0, 1, 0.55, "k", "LineStyle", "--");
text(ax, 0.6, 0, 0, "x");
text(ax, 0, 0.6, 0, "y");
text(ax, 0, 0, 0.6, "z");

xlabel(ax, "x");
ylabel(ax, "y");
zlabel(ax, "z");
title(ax, "Principal stress directions");
xlim(ax, [-1.2, 1.2]);
ylim(ax, [-1.2, 1.2]);
zlim(ax, [-1.2, 1.2]);
hold(ax, "off");
end
