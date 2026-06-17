function reactions = calcReaction(beam, support, loads)
%CALCREACTION 计算支座反力。
%
% 输入
%   beam    - 梁参数结构体，包含 L、E、I、yMax、n 等字段
%   support - 支座结构体，描述支座类型和位置
%   loads   - 载荷结构体数组，描述集中力、力偶和分布载荷
%
% 输出
%   reactions - 支反力结构体，包含 RA、RB、MA 等字段
%
% 支座类型说明：
%   "simply_supported" - 两个简单支座，位置为 xA 和 xB
%   "overhanging"      - 外伸梁，反力计算形式与简支梁相同
%   "cantilever"       - 左端固定悬臂梁，目前要求固定端 xA = 0

arguments
    beam struct
    support struct
    loads struct
end

% 读取支座类型；若用户没有填写 type，则默认按简支梁处理。
type = lower(string(beamGetField(support, "type", "simply_supported")));

% 将所有载荷转化为等效集中力、作用位置和集中力偶，便于列平衡方程。
[forceValues, forcePositions, momentValues] = beamLoadResultants(loads);

% 初始化反力结果。对不适用的字段保留为 0 或 NaN。
reactions = struct();
reactions.type = type;
reactions.RA = 0;
reactions.RB = 0;
reactions.MA = 0;
reactions.xA = beamGetField(support, "xA", 0);
reactions.xB = beamGetField(support, "xB", beam.L);
reactions.note = "";

totalForce = sum(forceValues);
totalMoment = sum(momentValues);

switch type
    case {"simply_supported", "overhanging"}
        % 简支梁和静定外伸梁都只有两个未知竖向反力，可由
        % sum(Fy)=0 和对 A 点取矩两个方程求得。
        xA = reactions.xA;
        xB = reactions.xB;

        if abs(xB - xA) < eps
            error("calcReaction:InvalidSupport", ...
                "The two support positions xA and xB must be different.");
        end

        % 集中力偶会直接加入弯矩图。这里让力偶项以相反符号进入
        % 支反力方程，使简支梁右支座处的内弯矩满足 M(xB)=0。
        momentAboutA = sum(forceValues .* (forcePositions - xA)) - totalMoment;
        reactions.RB = -momentAboutA / (xB - xA);
        reactions.RA = -totalForce - reactions.RB;

    case "cantilever"
        % 左端固定悬臂梁有一个竖向反力 RA 和一个固定端弯矩 MA。
        % RA 由竖向力平衡得到，MA 由自由端弯矩为零的条件得到。
        xA = reactions.xA;

        if abs(xA) > 1e-10
            error("calcReaction:UnsupportedCantilever", ...
                "This version supports a left fixed cantilever with xA = 0.");
        end

        reactions.xB = NaN;
        reactions.RA = -totalForce;

        % 选取 MA，使得自由端处弯矩为零。
        freeEnd = beam.L;
        reactions.MA = -(reactions.RA * (freeEnd - xA) ...
            + sum(forceValues .* (freeEnd - forcePositions)) ...
            + totalMoment);

    otherwise
        error("calcReaction:UnsupportedSupport", ...
            "Unsupported support type: %s", type);
end

% 保存外载荷合力与合力矩，便于调试和说明书中展示平衡检查。
reactions.totalExternalForce = totalForce;
reactions.totalExternalMoment = totalMoment;
end
