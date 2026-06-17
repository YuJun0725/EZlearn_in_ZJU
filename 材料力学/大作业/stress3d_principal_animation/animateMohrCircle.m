function animateMohrCircle(result, frameCount, pauseTime, unitName)
%ANIMATEMOHRCIRCLE Animate moving points on the three Mohr circles.

if nargin < 2
    frameCount = 100;
end
if nargin < 3
    pauseTime = 0.03;
end
if nargin < 4
    unitName = "";
end

s = result.principalStresses;
pairs = [1 2; 2 3; 1 3];
colors = [0.85 0.1 0.1; 0.1 0.55 0.1; 0.1 0.2 0.85];
labels = ["sigma1-sigma2", "sigma2-sigma3", "sigma1-sigma3"];

figure("Name", "Animation: Mohr circle stress variation", "Color", "w");
ax = axes;
hold(ax, "on");
grid(ax, "on");
axis(ax, "equal");

pointHandles = gobjects(3, 1);
for i = 1:3
    sa = s(pairs(i, 1));
    sb = s(pairs(i, 2));
    c = (sa + sb) / 2;
    r = abs(sa - sb) / 2;
    t = linspace(0, 2 * pi, 361);
    plot(ax, c + r * cos(t), r * sin(t), ...
        "LineWidth", 1.5, "Color", colors(i, :), "DisplayName", labels(i));
    pointHandles(i) = plot(ax, c + r, 0, "o", ...
        "MarkerFaceColor", colors(i, :), "MarkerEdgeColor", "k", ...
        "MarkerSize", 7, "HandleVisibility", "off");
end

plot(ax, s, [0, 0, 0], "ko", "MarkerFaceColor", "k", "HandleVisibility", "off");
xlabel(ax, sprintf("Normal stress sigma (%s)", unitName));
ylabel(ax, sprintf("Shear stress tau (%s)", unitName));
title(ax, "Moving points on three Mohr circles");
legend(ax, "Location", "best");

for k = 1:frameCount
    phi = 2 * pi * (k - 1) / max(frameCount - 1, 1);
    for i = 1:3
        sa = s(pairs(i, 1));
        sb = s(pairs(i, 2));
        c = (sa + sb) / 2;
        r = abs(sa - sb) / 2;
        set(pointHandles(i), "XData", c + r * cos(phi), "YData", r * sin(phi));
    end
    drawnow;
    pause(pauseTime);
end

hold(ax, "off");
end
