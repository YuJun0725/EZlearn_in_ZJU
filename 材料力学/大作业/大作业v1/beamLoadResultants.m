function [forceValues, forcePositions, momentValues] = beamLoadResultants(loads)
%BEAMLOADRESULTANTS 将载荷结构体转化为等效合力和力偶。
%
% 输出
%   forceValues    - 等效集中力大小，单位 N
%   forcePositions - 等效集中力作用位置，单位 m
%   momentValues   - 集中力偶，单位 N*m

forceValues = [];
forcePositions = [];
momentValues = [];

% 逐个载荷读取 type 字段，然后按照不同载荷类型等效。
for k = 1:numel(loads)
    loadType = lower(string(beamGetField(loads(k), "type", "")));

    switch loadType
        case "point"
            % 集中力本身就是等效合力，作用位置为输入的 x。
            forceValues(end + 1) = beamGetField(loads(k), "P", 0); %#ok<AGROW>
            forcePositions(end + 1) = beamGetField(loads(k), "x", 0); %#ok<AGROW>

        case {"moment", "couple"}
            % 集中力偶只参与力矩平衡，不参与竖向力平衡。
            momentValues(end + 1) = beamGetField(loads(k), ["M", "M0"], 0); %#ok<AGROW>

        case "udl"
            % 均布载荷等效为 F=q*(x2-x1)，作用点在区间中点。
            q = beamGetField(loads(k), "q", 0);
            x1 = beamGetField(loads(k), "x1", 0);
            x2 = beamGetField(loads(k), "x2", 0);
            if x2 < x1
                [x1, x2] = deal(x2, x1);
            end
            F = q * (x2 - x1);
            forceValues(end + 1) = F; %#ok<AGROW>
            forcePositions(end + 1) = (x1 + x2) / 2; %#ok<AGROW>

        case {"linear", "linear_udl", "trapezoid"}
            % 线性分布载荷等效为梯形面积，作用点由一阶矩确定。
            q1 = beamGetField(loads(k), ["q1", "qa", "qA"], 0);
            q2 = beamGetField(loads(k), ["q2", "qb", "qB"], 0);
            x1 = beamGetField(loads(k), "x1", 0);
            x2 = beamGetField(loads(k), "x2", 0);
            if x2 < x1
                [x1, x2] = deal(x2, x1);
                [q1, q2] = deal(q2, q1);
            end

            span = x2 - x1;
            F = 0.5 * (q1 + q2) * span;
            firstMoment = x1 * F + span ^ 2 * (q1 / 2 + (q2 - q1) / 3);

            forceValues(end + 1) = F; %#ok<AGROW>
            if abs(F) < eps
                forcePositions(end + 1) = (x1 + x2) / 2; %#ok<AGROW>
            else
                forcePositions(end + 1) = firstMoment / F; %#ok<AGROW>
            end

        otherwise
            error("beamLoadResultants:UnsupportedLoad", ...
                "Unsupported load type at index %d: %s", k, loadType);
    end
end
end
