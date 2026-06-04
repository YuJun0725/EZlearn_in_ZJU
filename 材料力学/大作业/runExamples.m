%% 典型算例脚本
% 本脚本用于一次性运行说明书中可展示的三个算例。
% 与 main.m 不同，本文件更适合作为“算例验证”部分的辅助程序。

clear;
clc;
close all;

% 每个算例写成一个局部函数，便于统一循环调用。
examples = {@exampleSimplySupportedPoint, @exampleCantileverPoint, ...
    @examplePartialUdl};

for k = 1:numel(examples)
    fprintf("\n========== Example %d ==========\n", k);
    result = examples{k}();
    printResultSummary(result);
    plotBeamResult(result);
end

function result = exampleSimplySupportedPoint()
% 算例一：简支梁跨中受向下集中力。
beam.L = 6.0;
beam.E = 210e9;
beam.I = 8.0e-6;
beam.yMax = 0.10;
beam.n = 1000;

support.type = "simply_supported";
support.xA = 0.0;
support.xB = beam.L;

loads = struct([]);
loads(1).type = "point";
loads(1).P = -10000;
loads(1).x = 3.0;

result = solveBeamCase(beam, support, loads);
end

function result = exampleCantileverPoint()
% 算例二：左端固定悬臂梁，自由端受向下集中力。
beam.L = 2.0;
beam.E = 210e9;
beam.I = 8.0e-6;
beam.yMax = 0.10;
beam.n = 1000;

support.type = "cantilever";
support.xA = 0.0;

loads = struct([]);
loads(1).type = "point";
loads(1).P = -2000;
loads(1).x = beam.L;

result = solveBeamCase(beam, support, loads);
end

function result = examplePartialUdl()
% 算例三：简支梁局部区间承受均布载荷。
beam.L = 8.0;
beam.E = 210e9;
beam.I = 8.0e-6;
beam.yMax = 0.10;
beam.n = 1200;

support.type = "simply_supported";
support.xA = 0.0;
support.xB = beam.L;

loads = struct([]);
loads(1).type = "udl";
loads(1).q = -3000;
loads(1).x1 = 2.0;
loads(1).x2 = 6.0;

result = solveBeamCase(beam, support, loads);
end

function result = solveBeamCase(beam, support, loads)
% 将 main.m 中的通用计算流程封装为函数，避免每个算例重复写代码。
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

function printResultSummary(result)
% 在命令行输出关键结果，便于和教材公式或手算结果比较。
[maxAbsV, idxV] = max(abs(result.V));
[maxAbsM, idxM] = max(abs(result.M));
[maxAbsW, idxW] = max(abs(result.deflection));

fprintf("RA = %.6g N\n", result.reactions.RA);
if isfield(result.reactions, "RB") && ~isnan(result.reactions.RB)
    fprintf("RB = %.6g N\n", result.reactions.RB);
end
if isfield(result.reactions, "MA") && abs(result.reactions.MA) > 0
    fprintf("MA = %.6g N*m\n", result.reactions.MA);
end
fprintf("max |V| = %.6g N at x = %.6g m\n", maxAbsV, result.x(idxV));
fprintf("max |M| = %.6g N*m at x = %.6g m\n", maxAbsM, result.x(idxM));
fprintf("max stress = %.6g Pa at x = %.6g m\n", ...
    result.stress.maxValue, result.x(result.stress.maxIndex));
fprintf("max |w| = %.6g m at x = %.6g m\n", maxAbsW, result.x(idxW));
end
