function [theta, deflection] = calcDeflection(beam, support, x, M)
%CALCDEFLECTION 计算转角和挠度。
%
% 输入
%   beam    - 梁参数结构体，需要包含 E 和 I
%   support - 支座条件结构体
%   x       - 梁长方向上的离散计算点
%   M       - 弯矩数组，单位 N*m
%
% 输出
%   theta      - 转角数组，单位 rad
%   deflection - 挠度数组，单位 m
%
arguments
    beam struct
    support struct
    x double
    M double
end

if beam.E <= 0 || beam.I <= 0
    error("calcDeflection:InvalidBeam", "E and I must be positive.");
end

% 根据 Euler-Bernoulli 梁理论：w'' = M/(EI)。
curvature = M ./ (beam.E * beam.I);

% 第一次积分得到未经边界条件修正的转角，第二次积分得到初始挠度。
theta0 = cumtrapz(x, curvature);
deflection0 = cumtrapz(x, theta0);

type = lower(string(beamGetField(support, "type", "simply_supported")));

switch type
    case {"simply_supported", "overhanging"}
        % 简支梁和静定外伸梁：两个支座处挠度为零。
        % 数值积分会带有两个未知积分常数，因此用 c1*x+c2 修正。
        xA = beamGetField(support, "xA", 0);
        xB = beamGetField(support, "xB", beam.L);
        wA = interp1(x, deflection0, xA, "linear", "extrap");
        wB = interp1(x, deflection0, xB, "linear", "extrap");

        c1 = -(wB - wA) / (xB - xA);
        c2 = -wA - c1 * xA;

    case "cantilever"
        % 左端固定悬臂梁：固定端挠度和转角都为零。
        xA = beamGetField(support, "xA", 0);
        thetaA = interp1(x, theta0, xA, "linear", "extrap");
        wA = interp1(x, deflection0, xA, "linear", "extrap");

        c1 = -thetaA;
        c2 = -wA - c1 * xA;

    otherwise
        error("calcDeflection:UnsupportedSupport", ...
            "Unsupported support type: %s", type);
end

% 加上积分常数修正，得到满足边界条件的转角和挠度曲线。
theta = theta0 + c1;
deflection = deflection0 + c1 .* x + c2;
end
