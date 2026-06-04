function [V, M] = calcInternalForce(beam, support, loads, reactions, x)
%CALCINTERNALFORCE 计算剪力和弯矩数组。
%
% 输入
%   beam      - 梁参数结构体
%   support   - 支座参数结构体
%   loads     - 载荷结构体数组
%   reactions - calcReaction 函数得到的支反力结果
%   x         - 梁长方向上的离散计算点
%
% 输出
%   V - 剪力数组，单位 N
%   M - 弯矩数组，单位 N*m
%
arguments
    beam struct
    support struct
    loads struct
    reactions struct
    x double
end

% 先建立与 x 同尺寸的零数组，后续按“左侧外力叠加”逐项累加。
V = zeros(size(x));
M = zeros(size(x));

type = lower(string(beamGetField(support, "type", reactions.type)));

switch type
    case {"simply_supported", "overhanging"}
        % 简支梁和外伸梁：两个支座反力都作为集中力加入内力计算。
        [V, M] = addPointForce(V, M, x, reactions.RA, reactions.xA);
        [V, M] = addPointForce(V, M, x, reactions.RB, reactions.xB);

    case "cantilever"
        % 悬臂梁：固定端既有竖向反力，也有固定端弯矩。
        [V, M] = addPointForce(V, M, x, reactions.RA, reactions.xA);
        M = addPointMoment(M, x, reactions.MA, reactions.xA);

    otherwise
        error("calcInternalForce:UnsupportedSupport", ...
            "Unsupported support type: %s", type);
end

% 遍历用户输入的所有载荷，按类型分别加入剪力图和弯矩图。
for k = 1:numel(loads)
    loadType = lower(string(beamGetField(loads(k), "type", "")));

    switch loadType
        case "point"
            P = beamGetField(loads(k), "P", 0);
            xP = beamGetField(loads(k), "x", 0);
            [V, M] = addPointForce(V, M, x, P, xP);

        case {"moment", "couple"}
            M0 = beamGetField(loads(k), ["M", "M0"], 0);
            xM = beamGetField(loads(k), "x", 0);
            M = addPointMoment(M, x, M0, xM);

        case "udl"
            q = beamGetField(loads(k), "q", 0);
            x1 = beamGetField(loads(k), "x1", 0);
            x2 = beamGetField(loads(k), "x2", beam.L);
            [V, M] = addUniformLoad(V, M, x, q, x1, x2);

        case {"linear", "linear_udl", "trapezoid"}
            q1 = beamGetField(loads(k), ["q1", "qa", "qA"], 0);
            q2 = beamGetField(loads(k), ["q2", "qb", "qB"], 0);
            x1 = beamGetField(loads(k), "x1", 0);
            x2 = beamGetField(loads(k), "x2", beam.L);
            [V, M] = addLinearLoad(V, M, x, q1, q2, x1, x2);

        otherwise
            error("calcInternalForce:UnsupportedLoad", ...
                "Unsupported load type at index %d: %s", k, loadType);
    end
end
end

function [V, M] = addPointForce(V, M, x, P, xP)
% 集中力 P 对 xP 右侧的剪力产生突变，对弯矩产生线性贡献。
mask = x >= xP;
V(mask) = V(mask) + P;
M(mask) = M(mask) + P .* (x(mask) - xP);
end

function M = addPointMoment(M, x, M0, xM)
% 集中力偶不改变剪力，只使 xM 右侧的弯矩发生突变。
mask = x >= xM;
M(mask) = M(mask) + M0;
end

function [V, M] = addUniformLoad(V, M, x, q, x1, x2)
% 均布载荷按有效作用长度 lx 累加贡献。
% 当截面还未进入载荷区间时 lx=0；进入后 lx=x-x1；超过后 lx=x2-x1。
if x2 < x1
    [x1, x2] = deal(x2, x1);
end

lx = min(x, x2) - x1;
lx = max(lx, 0);

V = V + q .* lx;
M = M + q .* lx .* (x - x1 - lx ./ 2);
end

function [V, M] = addLinearLoad(V, M, x, q1, q2, x1, x2)
% 线性分布载荷 q(s)=q1+k(s-x1)。这里直接对载荷函数积分，
% 分别得到它对剪力和弯矩的贡献。
if x2 < x1
    [x1, x2] = deal(x2, x1);
    [q1, q2] = deal(q2, q1);
end

span = x2 - x1;
if span <= 0
    return;
end

k = (q2 - q1) / span;
lx = min(x, x2) - x1;
lx = max(lx, 0);
xa = x - x1;

V = V + q1 .* lx + 0.5 .* k .* lx .^ 2;
M = M + q1 .* (xa .* lx - 0.5 .* lx .^ 2) ...
    + k .* (0.5 .* xa .* lx .^ 2 - lx .^ 3 ./ 3);
end
