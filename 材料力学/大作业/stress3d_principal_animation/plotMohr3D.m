function plotMohr3D(result, unitName)
%PLOTMOHR3D Draw three Mohr circles for 3D principal stresses.

if nargin < 2
    unitName = "";
end

s = result.principalStresses;
s1 = s(1);
s2 = s(2);
s3 = s(3);

figure("Name", "3D Mohr circles", "Color", "w");
ax = axes;
hold(ax, "on");
grid(ax, "on");
axis(ax, "equal");

drawCircle(ax, s1, s2, [0.85 0.1 0.1], "sigma1-sigma2");
drawCircle(ax, s2, s3, [0.1 0.55 0.1], "sigma2-sigma3");
drawCircle(ax, s1, s3, [0.1 0.2 0.85], "sigma1-sigma3");

plot(ax, [s1, s2, s3], [0, 0, 0], "ko", "MarkerFaceColor", "k");
text(ax, s1, 0, "  sigma1");
text(ax, s2, 0, "  sigma2");
text(ax, s3, 0, "  sigma3");

xlabel(ax, sprintf("Normal stress sigma (%s)", unitName));
ylabel(ax, sprintf("Shear stress tau (%s)", unitName));
title(ax, "Three-dimensional Mohr circles");
legend(ax, "Location", "best");
hold(ax, "off");
end

function drawCircle(ax, sa, sb, color, labelText)
c = (sa + sb) / 2;
r = abs(sa - sb) / 2;
t = linspace(0, 2 * pi, 361);
plot(ax, c + r * cos(t), r * sin(t), ...
    "LineWidth", 1.6, "Color", color, "DisplayName", labelText);
end
