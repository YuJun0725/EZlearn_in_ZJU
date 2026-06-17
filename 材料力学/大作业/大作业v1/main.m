%% 梁弯曲内力、应力与挠度计算主程序
% 本文件是整个项目的入口。用户通常只需要修改本文件中的 beam、
% support 和 loads 三类参数，然后运行 main 即可得到计算结果和图像。

clear;
clc;
close all;

%% 1. 梁的基本参数
% 单位统一：长度 m，力 N，应力 Pa。
beam.L = 6.0;              % 梁长，m
beam.E = 210e9;            % 弹性模量，Pa
beam.I = 8.0e-6;           % 截面惯性矩，m^4
beam.yMax = 0.10;          % 截面边缘到中性轴的最大距离，m
beam.n = 1000;             % 沿梁长方向的离散计算点数量

%% 2. 支座信息
% 当前程序支持的支座类型：
%   "simply_supported简支梁"
%   "cantilever悬臂梁"
%   "overhanging外伸梁"
support.type = "simply_supported";  % 简支梁
support.xA = 0.0;                   % A 支座位置
support.xB = beam.L;                % B 支座位置

%% 3. 载荷信息
% 符号约定：
%   向上的力为正，向下的力为负；
%   集中力偶的正负号按说明书中的弯矩正方向约定。
% loads 使用结构体数组保存，因此可以继续添加 loads(2)、loads(3) 等。
loads = struct([]);

loads(1).type = "point";   % 集中力
loads(1).P = -10000;       % 集中力大小，N；负号表示向下
loads(1).x = 3.0;          % 集中力作用位置，m

% 均布载荷示例，若需要使用可取消注释：
% loads(2).type = "udl";
% loads(2).q = -500;       % N/m
% loads(2).x1 = 1.0;       % m
% loads(2).x2 = 5.0;       % m

%% 4. 计算流程
% 第一步：根据整体静力平衡计算支座反力。
reactions = calcReaction(beam, support, loads);

% 第二步：离散梁长，并在每一个离散点计算剪力 V 和弯矩 M。
x = linspace(0, beam.L, beam.n);
[V, M] = calcInternalForce(beam, support, loads, reactions, x);

% 第三步：由弯矩计算截面边缘最大弯曲正应力。
stress = calcStress(beam, M);

% 第四步：由 EIw'' = M 数值积分得到转角和挠度。
[theta, deflection] = calcDeflection(beam, support, x, M);

% 将所有结果打包成一个 result 结构体，便于绘图和后续扩展。
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

%% 5. 结果输出与绘图
% abs 用于寻找绝对值最大的位置，因为剪力、弯矩和挠度可能为正或负。
[maxAbsV, idxV] = max(abs(V));
[maxAbsM, idxM] = max(abs(M));
[maxAbsW, idxW] = max(abs(deflection));

fprintf("Beam bending analysis finished.\n");
fprintf("Support reaction RA = %.6g N\n", reactions.RA);
if isfield(reactions, "RB") && ~isnan(reactions.RB)
    fprintf("Support reaction RB = %.6g N\n", reactions.RB);
end
if isfield(reactions, "MA") && abs(reactions.MA) > 0
    fprintf("Fixed-end moment MA = %.6g N*m\n", reactions.MA);
end
fprintf("Maximum |V| = %.6g N at x = %.6g m\n", maxAbsV, x(idxV));
fprintf("Maximum |M| = %.6g N*m at x = %.6g m\n", maxAbsM, x(idxM));
fprintf("Maximum bending stress = %.6g Pa at x = %.6g m\n", ...
    stress.maxValue, x(stress.maxIndex));
fprintf("Maximum |deflection| = %.6g m at x = %.6g m\n", maxAbsW, x(idxW));

plotBeamResult(result);
