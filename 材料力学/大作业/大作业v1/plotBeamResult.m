function plotBeamResult(result)
%PLOTBEAMRESULT 绘制载荷示意图、剪力图、弯矩图、应力图和挠度图。
%
% 输入
%   result - main.m 中打包得到的结果结构体
%
arguments
    result struct
end

% 使用 tiledlayout 将 5 张图放在同一个窗口中，便于对比观察。
figure("Name", "Beam Bending Analysis Result");

tiledlayout(5, 1);

nexttile;
drawLoadDiagram(result);
title("Beam and Loads");

nexttile;
plot(result.x, result.V, "LineWidth", 1.5);
grid on;
ylabel("V / N");
title("Shear Force Diagram");

nexttile;
plot(result.x, result.M, "LineWidth", 1.5);
grid on;
ylabel("M / N m");
title("Bending Moment Diagram");

nexttile;
plot(result.x, result.stress.sigma, "LineWidth", 1.5);
grid on;
ylabel("sigma / Pa");
title("Maximum Bending Stress");

nexttile;
plot(result.x, result.deflection, "LineWidth", 1.5);
grid on;
xlabel("x / m");
ylabel("w / m");
title("Deflection Curve");
end

function drawLoadDiagram(result)
% 绘制梁、支座和载荷的简化示意图。
beam = result.beam;
support = result.support;
loads = result.loads;

hold on;
plot([0, beam.L], [0, 0], "k-", "LineWidth", 2);

supportType = lower(string(beamGetField(support, "type", "simply_supported")));
drawSupport(beamGetField(support, "xA", 0), supportType);
if supportType ~= "cantilever" && isfield(support, "xB") && ~isnan(support.xB)
    drawSupport(support.xB, "simple");
end

for k = 1:numel(loads)
    loadType = lower(string(beamGetField(loads(k), "type", "")));
    switch loadType
        case "point"
            % 集中力用单个箭头表示。
            P = beamGetField(loads(k), "P", 0);
            xP = beamGetField(loads(k), "x", 0);
            drawForceArrow(xP, P);

        case {"moment", "couple"}
            % 集中力偶用文字标注其大小。
            M0 = beamGetField(loads(k), ["M", "M0"], 0);
            xM = beamGetField(loads(k), "x", 0);
            text(xM, 0.25, sprintf("M=%.3g", M0), ...
                "HorizontalAlignment", "center");

        case "udl"
            % 均布载荷用多个等长箭头近似表示。
            q = beamGetField(loads(k), "q", 0);
            x1 = beamGetField(loads(k), "x1", 0);
            x2 = beamGetField(loads(k), "x2", beam.L);
            xs = linspace(x1, x2, 9);
            for i = 1:numel(xs)
                drawForceArrow(xs(i), q);
            end

        case {"linear", "linear_udl", "trapezoid"}
            % 线性分布载荷用多个箭头表示，箭头方向反映正负号。
            q1 = beamGetField(loads(k), ["q1", "qa", "qA"], 0);
            q2 = beamGetField(loads(k), ["q2", "qb", "qB"], 0);
            x1 = beamGetField(loads(k), "x1", 0);
            x2 = beamGetField(loads(k), "x2", beam.L);
            xs = linspace(x1, x2, 9);
            qs = linspace(q1, q2, 9);
            for i = 1:numel(xs)
                drawForceArrow(xs(i), qs(i));
            end
    end
end

xlim([-0.05 * beam.L, 1.05 * beam.L]);
ylim([-1, 1]);
yticks([]);
grid on;
box on;
hold off;
end

function drawSupport(x, type)
% 简支支座用三角标记，固定端用粗竖线表示。
type = lower(string(type));
if type == "cantilever"
    plot([x, x], [-0.45, 0.45], "k-", "LineWidth", 3);
else
    plot(x, -0.08, "kv", "MarkerFaceColor", "k", "MarkerSize", 7);
end
end

function drawForceArrow(x, value)
% 按载荷正负决定箭头方向：负值向下，正值向上。
if value == 0
    return;
end

if value < 0
    quiver(x, 0.65, 0, -0.45, 0, "r", "LineWidth", 1.2, "MaxHeadSize", 0.8);
else
    quiver(x, -0.65, 0, 0.45, 0, "b", "LineWidth", 1.2, "MaxHeadSize", 0.8);
end
end
