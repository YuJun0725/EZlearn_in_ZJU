function stress = calcStress(beam, M)
%CALCSTRESS 计算梁截面边缘最大弯曲正应力。
%
% 输入
%   beam - 梁参数结构体，需要包含 I 和 yMax
%   M    - 弯矩数组，单位 N*m
%
% 输出
%   stress - 应力结果结构体，包含应力数组、最大值和最大值位置索引
%
arguments
    beam struct
    M double
end

if beam.I <= 0
    error("calcStress:InvalidSection", "The second moment of area I must be positive.");
end

% 弯曲正应力公式：sigma = M*y/I。
% 程序关注截面边缘最大应力，因此使用 abs(M)*yMax/I。
stress = struct();
stress.sigma = abs(M) .* beam.yMax ./ beam.I;
[stress.maxValue, stress.maxIndex] = max(stress.sigma);
stress.note = "sigma = abs(M) * yMax / I";
end
