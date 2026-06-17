function plotStressCube(S, titleText, R, unitName)
%PLOTSTRESSCUBE Create a figure and draw a stress element.

if nargin < 2
    titleText = "Stress element";
end
if nargin < 3
    R = eye(3);
end
if nargin < 4
    unitName = "";
end

figure("Name", char(titleText), "Color", "w");
ax = axes;
drawStressCube(ax, S, titleText, R, unitName);
end
