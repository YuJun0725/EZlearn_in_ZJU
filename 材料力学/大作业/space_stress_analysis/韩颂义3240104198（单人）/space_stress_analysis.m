

clear; clc; close all;
set(groot, 'defaultAxesFontName', 'Microsoft YaHei');
set(groot, 'defaultTextFontName', 'Microsoft YaHei');

%% 1. 输入区
% 单位：MPa。应力张量排列为：
% [x 向正应力, xy 面切应力, zx 面切应力;
%  xy 面切应力, y 向正应力, yz 面切应力;
%  zx 面切应力, yz 面切应力, z 向正应力]。
useDefaultExamples = true;

if useDefaultExamples
    examples(1).name = '算例一：三维空间耦合应力状态';
    examples(1).components = [55, 55, 20, 5, 40, 40];
    examples(1).planeNormal = [2; -1; 2];     % 任意斜截面的法向量

    examples(2).name = '算例二：平面应力状态';
    examples(2).components = [80, -20, 0, 30, 0, 0];
    examples(2).planeNormal = [1; 1; 0];      % 位于 xy 平面内的斜截面法向量
else
    sigma_x = input('请输入 sigma_x (MPa) = ');
    sigma_y = input('请输入 sigma_y (MPa) = ');
    sigma_z = input('请输入 sigma_z (MPa) = ');
    tau_xy  = input('请输入 tau_xy  (MPa) = ');
    tau_yz  = input('请输入 tau_yz  (MPa) = ');
    tau_zx  = input('请输入 tau_zx  (MPa) = ');
    planeNormal = input('请输入斜截面法向量 [nx; ny; nz] = ');
    examples(1).name = '自定义应力状态';
    examples(1).components = [sigma_x, sigma_y, sigma_z, tau_xy, tau_yz, tau_zx];
    examples(1).planeNormal = planeNormal;
end

makeAnimation = true;
animationExampleIndex = 1;
animationFrames = 90;
animationDelay = 0.06;

scriptDir = fileparts(mfilename('fullpath'));
if isempty(scriptDir)
    scriptDir = pwd;
end
outputDir = fullfile(scriptDir, 'results');
if ~exist(outputDir, 'dir')
    mkdir(outputDir);
end

%% 2. 主计算与图形输出
allResultText = cell(numel(examples), 1);

for exampleIndex = 1:numel(examples)
    exampleName = examples(exampleIndex).name;
    components = examples(exampleIndex).components;
    planeNormal = examples(exampleIndex).planeNormal;

    sigma_x = components(1);
    sigma_y = components(2);
    sigma_z = components(3);
    tau_xy  = components(4);
    tau_yz  = components(5);
    tau_zx  = components(6);

    S = [sigma_x, tau_xy,  tau_zx; ...
         tau_xy,  sigma_y, tau_yz; ...
         tau_zx,  tau_yz,  sigma_z];

    [principalStress, principalDir, Sprincipal] = calcPrincipalStress(S);
    invariants = calcStressInvariants(S, principalStress);
    [traction, normalStress, shearVector, shearStress, unitNormal] = ...
        calcSectionStress(S, planeNormal);

    resultText = formatResultText(exampleName, S, principalStress, principalDir, Sprincipal, ...
        invariants, unitNormal, traction, normalStress, shearVector, shearStress);
    allResultText{exampleIndex} = resultText;
    disp(resultText);

    caseTag = sprintf('case%d', exampleIndex);
    shortName = sprintf('算例%d', exampleIndex);

    fig1 = figure('Color', 'w', 'Name', [shortName, ' 原坐标方向应力单元']);
    ax1 = axes('Parent', fig1);
    drawStressCube(ax1, S, eye(3), [shortName, ' 原坐标方向应力单元']);
    saveFigure(fig1, fullfile(outputDir, [caseTag, '_original_stress_cube.png']));
    if exampleIndex == 1
        saveFigure(fig1, fullfile(outputDir, 'original_stress_cube.png'));
    end

    fig2 = figure('Color', 'w', 'Name', [shortName, ' 主方向应力单元']);
    ax2 = axes('Parent', fig2);
    drawStressCube(ax2, S, principalDir, [shortName, ' 主应力方向下的应力单元']);
    saveFigure(fig2, fullfile(outputDir, [caseTag, '_principal_stress_cube.png']));
    if exampleIndex == 1
        saveFigure(fig2, fullfile(outputDir, 'principal_stress_cube.png'));
    end

    fig3 = figure('Color', 'w', 'Name', [shortName, ' 主应力方向']);
    ax3 = axes('Parent', fig3);
    plotPrincipalDirections(ax3, principalDir, principalStress, [shortName, ' 主应力方向']);
    saveFigure(fig3, fullfile(outputDir, [caseTag, '_principal_directions.png']));
    if exampleIndex == 1
        saveFigure(fig3, fullfile(outputDir, 'principal_directions.png'));
    end

    fig4 = figure('Color', 'w', 'Name', [shortName, ' 三维莫尔圆']);
    ax4 = axes('Parent', fig4);
    plotMohrCircles(ax4, principalStress, [shortName, ' 三维应力状态莫尔圆']);
    saveFigure(fig4, fullfile(outputDir, [caseTag, '_mohr_circles.png']));
    if exampleIndex == 1
        saveFigure(fig4, fullfile(outputDir, 'mohr_circles.png'));
    end

    if makeAnimation && exampleIndex == animationExampleIndex
        gifFile = fullfile(outputDir, [caseTag, '_principal_rotation_animation.gif']);
        animatePrincipalRotation(S, principalDir, animationFrames, animationDelay, gifFile);
        if exampleIndex == 1
            copyfile(gifFile, fullfile(outputDir, 'principal_rotation_animation.gif'));
        end
    end
end

resultFile = fullfile(outputDir, 'principal_results.txt');
fid = fopen(resultFile, 'w');
fprintf(fid, '%s', strjoin(allResultText, [newline, newline]));
fclose(fid);

fprintf('\n结果文件已保存到：\n%s\n', outputDir);

%% 局部函数
function [principalStress, principalDir, Sprincipal] = calcPrincipalStress(S)
    [V, D] = eig(S);
    stressValues = diag(D);
    [principalStress, idx] = sort(stressValues, 'descend');
    principalDir = V(:, idx);

    for k = 1:3
        [~, maxIdx] = max(abs(principalDir(:, k)));
        if principalDir(maxIdx, k) < 0
            principalDir(:, k) = -principalDir(:, k);
        end
    end

    Sprincipal = principalDir.' * S * principalDir;
    Sprincipal(abs(Sprincipal) < 1e-10) = 0;
end

function invariants = calcStressInvariants(S, principalStress)
    sx = S(1, 1);
    sy = S(2, 2);
    sz = S(3, 3);
    txy = S(1, 2);
    tyz = S(2, 3);
    tzx = S(1, 3);

    invariants.I1 = trace(S);
    invariants.I2 = sx * sy + sy * sz + sz * sx - txy^2 - tyz^2 - tzx^2;
    invariants.I3 = det(S);
    invariants.meanStress = invariants.I1 / 3;
    invariants.maxShear = (principalStress(1) - principalStress(3)) / 2;
    invariants.vonMises = sqrt(((principalStress(1) - principalStress(2))^2 + ...
        (principalStress(2) - principalStress(3))^2 + ...
        (principalStress(3) - principalStress(1))^2) / 2);
end

function [traction, normalStress, shearVector, shearStress, unitNormal] = ...
    calcSectionStress(S, planeNormal)
    if norm(planeNormal) < eps
        error('斜截面法向量不能为零向量。');
    end
    unitNormal = planeNormal(:) / norm(planeNormal);
    traction = S * unitNormal;
    normalStress = unitNormal.' * traction;
    shearVector = traction - normalStress * unitNormal;
    shearStress = norm(shearVector);
end

function text = formatResultText(exampleName, S, principalStress, principalDir, Sprincipal, ...
    invariants, unitNormal, traction, normalStress, shearVector, shearStress)
    lines = {};
    lines{end + 1} = '================ 空间应力状态分析结果 ================';
    lines{end + 1} = exampleName;
    lines{end + 1} = '';
    lines{end + 1} = '应力张量 sigma (MPa)：';
    lines{end + 1} = matrixToText(S);
    lines{end + 1} = '';
    lines{end + 1} = '主应力（MPa，按从大到小排序）：';
    for k = 1:3
        lines{end + 1} = sprintf('sigma_%d = %12.6f', k, principalStress(k));
    end
    lines{end + 1} = '';
    lines{end + 1} = '主方向在原 x-y-z 坐标系中的方向余弦：';
    lines{end + 1} = '             x方向余弦     y方向余弦     z方向余弦';
    for k = 1:3
        lines{end + 1} = sprintf('方向_%d  %12.6f %12.6f %12.6f', ...
            k, principalDir(1, k), principalDir(2, k), principalDir(3, k));
    end
    lines{end + 1} = '';
    lines{end + 1} = '变换到主坐标系后的应力张量（MPa）：';
    lines{end + 1} = matrixToText(Sprincipal);
    lines{end + 1} = '';
    lines{end + 1} = sprintf('I1 = %.6f MPa', invariants.I1);
    lines{end + 1} = sprintf('I2 = %.6f MPa^2', invariants.I2);
    lines{end + 1} = sprintf('I3 = %.6f MPa^3', invariants.I3);
    lines{end + 1} = sprintf('平均应力 = %.6f MPa', invariants.meanStress);
    lines{end + 1} = sprintf('最大切应力 = %.6f MPa', invariants.maxShear);
    lines{end + 1} = sprintf('von Mises 等效应力 = %.6f MPa', invariants.vonMises);
    lines{end + 1} = '';
    lines{end + 1} = '指定斜截面上的应力：';
    lines{end + 1} = sprintf('单位法向量 n = [%.6f, %.6f, %.6f]^T', unitNormal);
    lines{end + 1} = sprintf('全应力矢量 T = [%.6f, %.6f, %.6f]^T MPa', traction);
    lines{end + 1} = sprintf('正应力 sigma_n = %.6f MPa', normalStress);
    lines{end + 1} = sprintf('切应力矢量 tau_n = [%.6f, %.6f, %.6f]^T MPa', shearVector);
    lines{end + 1} = sprintf('切应力大小 |tau_n| = %.6f MPa', shearStress);
    lines{end + 1} = '=============================================================';
    text = strjoin(lines, newline);
end

function text = matrixToText(A)
    text = sprintf('[%12.6f %12.6f %12.6f\n %12.6f %12.6f %12.6f\n %12.6f %12.6f %12.6f]', ...
        A(1, 1), A(1, 2), A(1, 3), ...
        A(2, 1), A(2, 2), A(2, 3), ...
        A(3, 1), A(3, 2), A(3, 3));
end

function drawStressCube(ax, S, R, titleText)
    cla(ax);
    hold(ax, 'on');
    axis(ax, 'equal');
    axis(ax, [-1.15 1.15 -1.15 1.15 -1.15 1.15]);
    grid(ax, 'on');
    view(ax, 38, 24);
    xlabel(ax, 'x 轴');
    ylabel(ax, 'y 轴');
    zlabel(ax, 'z 轴');
    title(ax, titleText);

    verticesLocal = 0.5 * [-1 -1 -1;
                            1 -1 -1;
                            1  1 -1;
                           -1  1 -1;
                           -1 -1  1;
                            1 -1  1;
                            1  1  1;
                           -1  1  1].';
    vertices = (R * verticesLocal).';
    faces = [1 2 3 4;
             5 6 7 8;
             1 2 6 5;
             2 3 7 6;
             3 4 8 7;
             4 1 5 8];

    patch(ax, 'Vertices', vertices, 'Faces', faces, ...
        'FaceColor', [0.78 0.88 1.00], 'FaceAlpha', 0.18, ...
        'EdgeColor', [0.10 0.18 0.25], 'LineWidth', 1.2);

    localNormals = [ 0  0 -1;
                     0  0  1;
                     0 -1  0;
                     1  0  0;
                     0  1  0;
                    -1  0  0].';
    maxStress = max(abs(eig(S)));
    if maxStress < eps
        maxStress = 1;
    end
    arrowScale = 0.55 / maxStress;

    for i = 1:size(localNormals, 2)
        normalGlobal = R * localNormals(:, i);
        center = 0.5 * normalGlobal;
        traction = S * normalGlobal;
        quiver3(ax, center(1), center(2), center(3), ...
            arrowScale * traction(1), arrowScale * traction(2), arrowScale * traction(3), ...
            0, 'Color', [0.86 0.16 0.10], 'LineWidth', 2.0, 'MaxHeadSize', 0.8);
        quiver3(ax, center(1), center(2), center(3), ...
            0.18 * normalGlobal(1), 0.18 * normalGlobal(2), 0.18 * normalGlobal(3), ...
            0, 'Color', [0.20 0.20 0.20], 'LineStyle', ':', 'LineWidth', 1.0);
    end

    drawGlobalAxes(ax);
    hold(ax, 'off');
end

function drawGlobalAxes(ax)
    quiver3(ax, 0, 0, 0, 0.9, 0, 0, 0, 'Color', [0.15 0.30 0.80], 'LineWidth', 1.4);
    quiver3(ax, 0, 0, 0, 0, 0.9, 0, 0, 'Color', [0.00 0.55 0.20], 'LineWidth', 1.4);
    quiver3(ax, 0, 0, 0, 0, 0, 0.9, 0, 'Color', [0.55 0.20 0.75], 'LineWidth', 1.4);
    text(ax, 0.95, 0, 0, 'x', 'Color', [0.15 0.30 0.80], 'FontWeight', 'bold');
    text(ax, 0, 0.95, 0, 'y', 'Color', [0.00 0.55 0.20], 'FontWeight', 'bold');
    text(ax, 0, 0, 0.95, 'z', 'Color', [0.55 0.20 0.75], 'FontWeight', 'bold');
end

function plotPrincipalDirections(ax, principalDir, principalStress, titleText)
    cla(ax);
    hold(ax, 'on');
    axis(ax, 'equal');
    axis(ax, [-1.1 1.1 -1.1 1.1 -1.1 1.1]);
    grid(ax, 'on');
    view(ax, 38, 24);
    xlabel(ax, 'x 轴');
    ylabel(ax, 'y 轴');
    zlabel(ax, 'z 轴');
    title(ax, titleText);
    drawGlobalAxes(ax);

    colors = [0.86 0.16 0.10;
              0.08 0.45 0.82;
              0.05 0.58 0.35];
    for k = 1:3
        v = principalDir(:, k);
        quiver3(ax, 0, 0, 0, v(1), v(2), v(3), 0, ...
            'Color', colors(k, :), 'LineWidth', 2.8, 'MaxHeadSize', 0.55);
        text(ax, 1.08 * v(1), 1.08 * v(2), 1.08 * v(3), ...
            sprintf('\\sigma_%d = %.1f MPa', k, principalStress(k)), ...
            'Color', colors(k, :), 'FontWeight', 'bold');
    end
    hold(ax, 'off');
end

function plotMohrCircles(ax, principalStress, titleText)
    cla(ax);
    hold(ax, 'on');
    grid(ax, 'on');
    axis(ax, 'equal');
    xlabel(ax, '正应力 \sigma / MPa');
    ylabel(ax, '切应力 \tau / MPa');
    title(ax, titleText);

    theta = linspace(0, 2 * pi, 500);
    pairs = [1 2; 2 3; 1 3];
    colors = [0.08 0.45 0.82;
              0.05 0.58 0.35;
              0.86 0.16 0.10];
    labels = {'\sigma_1 - \sigma_2', '\sigma_2 - \sigma_3', '\sigma_1 - \sigma_3'};

    for k = 1:3
        i = pairs(k, 1);
        j = pairs(k, 2);
        center = (principalStress(i) + principalStress(j)) / 2;
        radius = abs(principalStress(i) - principalStress(j)) / 2;
        sigma = center + radius * cos(theta);
        tau = radius * sin(theta);
        plot(ax, sigma, tau, 'Color', colors(k, :), 'LineWidth', 1.8, ...
            'DisplayName', labels{k});
    end
    plot(ax, principalStress, zeros(3, 1), 'ko', 'MarkerFaceColor', 'k', ...
        'DisplayName', '主应力');
    legend(ax, 'Location', 'best');
    hold(ax, 'off');
end

function animatePrincipalRotation(S, principalDir, frameCount, delayTime, gifFile)
    fig = figure('Color', 'w', 'Name', '主应力方向旋转动画', ...
        'Position', [80 80 1120 520]);
    layout = tiledlayout(fig, 1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

    axCube = nexttile(layout, 1);
    axPlot = nexttile(layout, 2);
    targetR = principalDir;
    if det(targetR) < 0
        targetR(:, 2) = -targetR(:, 2);
    end
    [U, ~, V] = svd(targetR);
    targetR = U * V.';
    if det(targetR) < 0
        U(:, 3) = -U(:, 3);
        targetR = U * V.';
    end

    shearHistory = zeros(frameCount, 1);
    progressHistory = linspace(0, 1, frameCount);

    for k = 1:frameCount
        s = progressHistory(k);
        smoothS = 3 * s^2 - 2 * s^3;
        R = interpolateRotation(targetR, smoothS);
        Sloc = R.' * S * R;
        shearHistory(k) = sqrt(sum(sum((Sloc - diag(diag(Sloc))).^2)) / 2);

        drawStressCube(axCube, S, R, sprintf('向主方向旋转：%.0f%%', 100 * s));

        cla(axPlot);
        hold(axPlot, 'on');
        grid(axPlot, 'on');
        plot(axPlot, progressHistory(1:k), shearHistory(1:k), ...
            'Color', [0.86 0.16 0.10], 'LineWidth', 2.0);
        xlabel(axPlot, '动画进度');
        ylabel(axPlot, '非对角切应力度量 / MPa');
        title(axPlot, '主坐标系中切应力逐渐消失');
        xlim(axPlot, [0 1]);
        ylim(axPlot, [0, max(1, 1.08 * max(shearHistory(1:k)))]);

        matrixText = sprintf(['当前旋转坐标系中的应力张量 (MPa)\n', ...
            '[%7.2f %7.2f %7.2f\n %7.2f %7.2f %7.2f\n %7.2f %7.2f %7.2f]'], ...
            Sloc(1, 1), Sloc(1, 2), Sloc(1, 3), ...
            Sloc(2, 1), Sloc(2, 2), Sloc(2, 3), ...
            Sloc(3, 1), Sloc(3, 2), Sloc(3, 3));
        text(axPlot, 0.04, 0.94, matrixText, 'Units', 'normalized', ...
            'VerticalAlignment', 'top', 'FontName', 'Microsoft YaHei', ...
            'BackgroundColor', [1 1 1], 'EdgeColor', [0.75 0.75 0.75]);
        hold(axPlot, 'off');

        drawnow;
        frame = getframe(fig);
        [imageData, map] = rgb2ind(frame2im(frame), 256);
        if k == 1
            imwrite(imageData, map, gifFile, 'gif', 'LoopCount', Inf, 'DelayTime', delayTime);
        else
            imwrite(imageData, map, gifFile, 'gif', 'WriteMode', 'append', 'DelayTime', delayTime);
        end
    end
end

function R = interpolateRotation(targetR, s)
    cosTheta = (trace(targetR) - 1) / 2;
    cosTheta = min(1, max(-1, cosTheta));
    theta = acos(cosTheta);

    if abs(theta) < 1e-12
        R = eye(3);
        return;
    end

    axisVector = [targetR(3, 2) - targetR(2, 3);
                  targetR(1, 3) - targetR(3, 1);
                  targetR(2, 1) - targetR(1, 2)] / (2 * sin(theta));
    axisVector = axisVector / norm(axisVector);
    R = axisAngleToMatrix(axisVector, s * theta);
end

function R = axisAngleToMatrix(axisVector, theta)
    x = axisVector(1);
    y = axisVector(2);
    z = axisVector(3);
    K = [ 0 -z  y;
          z  0 -x;
         -y  x  0];
    R = eye(3) + sin(theta) * K + (1 - cos(theta)) * (K * K);
end

function saveFigure(fig, fileName)
    try
        exportgraphics(fig, fileName, 'Resolution', 180);
    catch
        print(fig, fileName, '-dpng', '-r180');
    end
end
