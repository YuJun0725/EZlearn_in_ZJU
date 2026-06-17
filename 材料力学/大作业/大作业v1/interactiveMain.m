%% 交互式梁弯曲计算程序
% 运行本文件后，程序会在命令行中逐步询问梁参数、支座类型和载荷信息。
% 计算核心仍然复用 calcReaction、calcInternalForce、calcStress、
% calcDeflection 和 plotBeamResult 等函数。

clear;
clc;
close all;

fprintf("========================================\n");
fprintf("  梁弯曲内力、应力与挠度交互式计算程序\n");
fprintf("========================================\n\n");
fprintf("符号约定：向上为正，向下为负。\n");
fprintf("例如：向下 10000 N 的集中力请输入 -10000。\n\n");

beam = readBeamInput();
support = readSupportInput(beam);
loads = readLoadInput(beam);

result = solveBeamInteractive(beam, support, loads);
printInteractiveSummary(result);
plotBeamResult(result);

function beam = readBeamInput()
% 读取梁的基本参数。
fprintf("一、输入梁的基本参数\n");

beam.L = readPositiveNumber("梁长 L / m", 6.0);
beam.E = readPositiveNumber("弹性模量 E / Pa", 210e9);
beam.I = readPositiveNumber("截面惯性矩 I / m^4", 8.0e-6);
beam.yMax = readPositiveNumber("截面边缘距离 yMax / m", 0.10);
beam.n = round(readPositiveNumber("离散计算点数量 n", 1000));

if beam.n < 10
    fprintf("离散点数量过小，已自动改为 10。\n");
    beam.n = 10;
end

fprintf("\n");
end

function support = readSupportInput(beam)
% 读取支座类型和支座位置。
fprintf("二、选择支座类型\n");
fprintf("1 - 简支梁 simply_supported\n");
fprintf("2 - 悬臂梁 cantilever\n");
fprintf("3 - 外伸梁 overhanging\n");

choice = readIntegerInRange("支座类型编号", 1, 1, 3);

switch choice
    case 1
        support.type = "simply_supported";
        support.xA = readPosition("A 支座位置 xA / m", 0.0, beam.L);
        support.xB = readPosition("B 支座位置 xB / m", beam.L, beam.L);
        support = ensureDifferentSupports(support, beam);

    case 2
        support.type = "cantilever";
        fprintf("当前程序支持左端固定悬臂梁，因此固定端位置取 xA = 0。\n");
        support.xA = 0.0;

    case 3
        support.type = "overhanging";
        support.xA = readPosition("A 支座位置 xA / m", beam.L / 3, beam.L);
        support.xB = readPosition("B 支座位置 xB / m", 2 * beam.L / 3, beam.L);
        support = ensureDifferentSupports(support, beam);
end

fprintf("\n");
end

function loads = readLoadInput(beam)
% 读取多个载荷。每个载荷用 loads(k) 结构体保存。
fprintf("三、输入载荷信息\n");
loadCount = readIntegerInRange("载荷个数", 1, 0, 100);
loads = struct([]);

for k = 1:loadCount
    fprintf("\n第 %d 个载荷：\n", k);
    fprintf("1 - 集中力 point\n");
    fprintf("2 - 集中力偶 moment\n");
    fprintf("3 - 均布载荷 udl\n");
    fprintf("4 - 线性分布载荷 linear\n");

    loadTypeChoice = readIntegerInRange("载荷类型编号", 1, 1, 4);

    switch loadTypeChoice
        case 1
            loads(k).type = "point";
            loads(k).P = readNumber("集中力 P / N", -10000);
            loads(k).x = readPosition("作用位置 x / m", beam.L / 2, beam.L);

        case 2
            loads(k).type = "moment";
            loads(k).M = readNumber("集中力偶 M / (N*m)", 1000);
            loads(k).x = readPosition("作用位置 x / m", beam.L / 2, beam.L);

        case 3
            loads(k).type = "udl";
            loads(k).q = readNumber("均布载荷集度 q / (N/m)", -1000);
            [x1, x2] = readLoadRange(beam);
            loads(k).x1 = x1;
            loads(k).x2 = x2;

        case 4
            loads(k).type = "linear";
            loads(k).q1 = readNumber("起点载荷集度 q1 / (N/m)", 0);
            loads(k).q2 = readNumber("终点载荷集度 q2 / (N/m)", -1000);
            [x1, x2] = readLoadRange(beam);
            loads(k).x1 = x1;
            loads(k).x2 = x2;
    end
end

fprintf("\n");
end

function result = solveBeamInteractive(beam, support, loads)
% 复用主程序中的通用计算流程。
reactions = calcReaction(beam, support, loads);
x = linspace(0, beam.L, beam.n);
[V, M] = calcInternalForce(beam, support, loads, reactions, x);
stress = calcStress(beam, M);
[theta, deflection] = calcDeflection(beam, support, x, M);

result.beam = beam;
result.support = support;
result.loads = loads;
result.reactions = reactions;
result.x = x;
result.V = V;
result.M = M;
result.stress = stress;
result.theta = theta;
result.deflection = deflection;
end

function printInteractiveSummary(result)
% 输出关键结果。
[maxAbsV, idxV] = max(abs(result.V));
[maxAbsM, idxM] = max(abs(result.M));
[maxAbsW, idxW] = max(abs(result.deflection));

fprintf("四、计算结果\n");
fprintf("RA = %.6g N\n", result.reactions.RA);
if isfield(result.reactions, "RB") && ~isnan(result.reactions.RB)
    fprintf("RB = %.6g N\n", result.reactions.RB);
end
if isfield(result.reactions, "MA") && abs(result.reactions.MA) > 0
    fprintf("MA = %.6g N*m\n", result.reactions.MA);
end
fprintf("最大 |V| = %.6g N，位置 x = %.6g m\n", maxAbsV, result.x(idxV));
fprintf("最大 |M| = %.6g N*m，位置 x = %.6g m\n", maxAbsM, result.x(idxM));
fprintf("最大弯曲正应力 = %.6g Pa，位置 x = %.6g m\n", ...
    result.stress.maxValue, result.x(result.stress.maxIndex));
fprintf("最大 |挠度| = %.6g m，位置 x = %.6g m\n", maxAbsW, result.x(idxW));
end

function value = readNumber(label, defaultValue)
% 读取数值输入。直接回车时采用默认值。
while true
    text = input(sprintf("%s [默认 %.6g] = ", label, defaultValue), "s");
    text = strtrim(text);

    if isempty(text)
        value = defaultValue;
        return;
    end

    value = str2double(text);
    if ~isnan(value) && isfinite(value)
        return;
    end

    fprintf("输入无效，请输入一个数字。\n");
end
end

function value = readPositiveNumber(label, defaultValue)
% 读取正数输入。
while true
    value = readNumber(label, defaultValue);
    if value > 0
        return;
    end
    fprintf("该参数必须大于 0，请重新输入。\n");
end
end

function value = readIntegerInRange(label, defaultValue, minValue, maxValue)
% 读取指定范围内的整数。
while true
    value = round(readNumber(label, defaultValue));
    if value >= minValue && value <= maxValue
        return;
    end
    fprintf("请输入 %d 到 %d 之间的整数。\n", minValue, maxValue);
end
end

function x = readPosition(label, defaultValue, L)
% 读取梁上位置，并限制在 0 到 L 范围内。
while true
    x = readNumber(label, defaultValue);
    if x >= 0 && x <= L
        return;
    end
    fprintf("位置必须在 0 到 %.6g m 之间，请重新输入。\n", L);
end
end

function [x1, x2] = readLoadRange(beam)
% 读取分布载荷作用区间，并保证 x2 大于 x1。
while true
    x1 = readPosition("载荷起点 x1 / m", 0.0, beam.L);
    x2 = readPosition("载荷终点 x2 / m", beam.L, beam.L);
    if x2 > x1
        return;
    end
    fprintf("载荷终点 x2 必须大于起点 x1，请重新输入。\n");
end
end

function support = ensureDifferentSupports(support, beam)
% 检查两个支座位置不能重合。
while abs(support.xB - support.xA) < eps
    fprintf("A、B 两个支座位置不能相同，请重新输入 B 支座位置。\n");
    support.xB = readPosition("B 支座位置 xB / m", beam.L, beam.L);
end
end
