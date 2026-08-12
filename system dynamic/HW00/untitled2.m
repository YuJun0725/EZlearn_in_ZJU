clear;
clc;
close all;

%% 系统参数
R = 0.250;          % m
k = 150;            % N/m
I = 2;              % kg*m^2
theta0 = 0;         % rad
thetaDot0 = 10;     % rad/s

%% 原系统：临界阻尼
Ktheta = 4*k*R^2;                     % 等效扭转刚度
omega_n = sqrt(Ktheta/I);             % 无阻尼固有频率
c_cr = 2*sqrt(I*Ktheta)/R^2;          % 临界阻尼器系数

% 临界阻尼响应
theta_cr = @(t) thetaDot0 .* t .* exp(-omega_n.*t);

% 最大响应及其发生时间
tmax_cr = 1/omega_n;
thetaMax_cr = theta_cr(tmax_cr);

% 峰值的10%
theta10_cr = 0.1*thetaMax_cr;

% 求峰值后第一次下降到最大值10%的时间
fun_cr = @(t) theta_cr(t) - theta10_cr;
t10_cr = fzero(fun_cr, [tmax_cr, 3]);

%% 改变参数：k增加到300 N/m，保持c不变
k2 = 300;                          % N/m
c2 = c_cr;                         % N*s/m

Ktheta2 = 4*k2*R^2;
Ctheta2 = c2*R^2;

omega_n2 = sqrt(Ktheta2/I);
zeta2 = Ctheta2/(2*sqrt(I*Ktheta2));
omega_d2 = omega_n2*sqrt(1-zeta2^2);

% 欠阻尼响应的一般系数
A2 = theta0;
B2 = (thetaDot0 + zeta2*omega_n2*theta0)/omega_d2;

theta_2 = @(t) exp(-zeta2*omega_n2.*t) .* ...
    (A2*cos(omega_d2.*t) + B2*sin(omega_d2.*t));

% 第一次正峰值
% 对本题theta0=0，可使用下式确定峰值时刻
tmax_2 = atan(omega_d2/(zeta2*omega_n2))/omega_d2;
thetaMax_2 = theta_2(tmax_2);

% 峰值的10%
theta10_2 = 0.1*thetaMax_2;

% 第一个过零点，用于限制fzero搜索区间
tzero_2 = pi/omega_d2;

% 求峰值后、第一次过零前下降到峰值10%的时刻
fun_2 = @(t) theta_2(t) - theta10_2;
t10_2 = fzero(fun_2, [tmax_2, tzero_2]);

%% 时间范围
tEnd = 2.0;
t = linspace(0, tEnd, 2000);

%% 图1：临界阻尼响应
figure('Color', 'w');

plot(t, theta_cr(t), 'b-', 'LineWidth', 2);
hold on;

plot(tmax_cr, thetaMax_cr, 'ro', ...
    'MarkerFaceColor', 'r', 'MarkerSize', 7);

plot(t10_cr, theta10_cr, 'ks', ...
    'MarkerFaceColor', 'y', 'MarkerSize', 7);

yline(theta10_cr, 'k--', ...
    '10% of maximum', 'LineWidth', 1.2);

xline(tmax_cr, 'r:', 't_{max}', 'LineWidth', 1.2);
xline(t10_cr, 'k:', 't_{10%}', 'LineWidth', 1.2);

grid on;
box on;
xlabel('Time t (s)');
ylabel('Angular displacement \theta(t) (rad)');
title('Critical damping response');
legend('\theta(t)', 'Maximum response', ...
    'First 10% point after peak', 'Location', 'northeast');

%% 图2：改变刚度后的欠阻尼响应
figure('Color', 'w');

plot(t, theta_2(t), 'm-', 'LineWidth', 2);
hold on;

plot(tmax_2, thetaMax_2, 'ro', ...
    'MarkerFaceColor', 'r', 'MarkerSize', 7);

plot(t10_2, theta10_2, 'ks', ...
    'MarkerFaceColor', 'y', 'MarkerSize', 7);

yline(theta10_2, 'k--', ...
    '10% of maximum', 'LineWidth', 1.2);

xline(tmax_2, 'r:', 't_{max}', 'LineWidth', 1.2);
xline(t10_2, 'k:', 't_{10%}', 'LineWidth', 1.2);

yline(0, 'k-', 'LineWidth', 0.8);

grid on;
box on;
xlabel('Time t (s)');
ylabel('Angular displacement \theta(t) (rad)');
title('Response after increasing stiffness to k = 300 N/m');
legend('\theta(t)', 'Maximum response', ...
    'First 10% point after peak', 'Location', 'northeast');

%% 图3：改变参数前后的响应对比
figure('Color', 'w');

plot(t, theta_cr(t), 'b-', 'LineWidth', 2);
hold on;
plot(t, theta_2(t), 'm--', 'LineWidth', 2);

plot(tmax_cr, thetaMax_cr, 'bo', ...
    'MarkerFaceColor', 'b', 'MarkerSize', 6);
plot(tmax_2, thetaMax_2, 'mo', ...
    'MarkerFaceColor', 'm', 'MarkerSize', 6);

plot(t10_cr, theta10_cr, 'bs', ...
    'MarkerFaceColor', 'c', 'MarkerSize', 6);
plot(t10_2, theta10_2, 'ms', ...
    'MarkerFaceColor', 'y', 'MarkerSize', 6);

yline(0, 'k-', 'LineWidth', 0.8);

grid on;
box on;
xlabel('Time t (s)');
ylabel('Angular displacement \theta(t) (rad)');
title('Comparison before and after changing stiffness');

legend('k = 150 N/m, critical damping', ...
       'k = 300 N/m, c unchanged', ...
       'Original maximum', ...
       'Modified maximum', ...
       'Original 10% point', ...
       'Modified 10% point', ...
       'Location', 'northeast');

%% 输出计算结果
fprintf('---------- Original critical damping system ----------\n');
fprintf('Critical damping coefficient c_cr = %.4f N*s/m\n', c_cr);
fprintf('Natural frequency omega_n        = %.4f rad/s\n', omega_n);
fprintf('Maximum-response time t_max       = %.4f s\n', tmax_cr);
fprintf('Maximum response theta_max        = %.4f rad\n', thetaMax_cr);
fprintf('First 10%% time after peak         = %.4f s\n\n', t10_cr);

fprintf('---------- Modified system: k = %.1f N/m ----------\n', k2);
fprintf('Natural frequency omega_n         = %.4f rad/s\n', omega_n2);
fprintf('Damping ratio zeta                = %.4f\n', zeta2);
fprintf('Damped frequency omega_d          = %.4f rad/s\n', omega_d2);
fprintf('Maximum-response time t_max       = %.4f s\n', tmax_2);
fprintf('Maximum response theta_max        = %.4f rad\n', thetaMax_2);
fprintf('First 10%% time after peak         = %.4f s\n', t10_2);
