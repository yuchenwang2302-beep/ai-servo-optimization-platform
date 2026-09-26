function f = fun_position_2(x,T)
simOut = simulate_servo_position(x, T, 'Jerk_FF_Step_2023_2');

% 索引
reference0 = simOut.Ref_Step_PU0.signals.values;
reference1 = simOut.Ref_Step_PU1.signals.values;
position = simOut.Pos_Fb_PU.signals.values;
time= simOut.Pos_Fb_PU.time;

time_step_idx = find(time >= 0.5,1);

% 设定稳态时间窗口 (例如最后0.15秒)
steady_state_window = time(end) - 0.15;  % 假设最后2秒是稳态

% 找到时间窗口的索引
steady_state_indices = find(time >= steady_state_window);

% 计算在稳态时间段内的平均值
steady_state_value = mean(position(steady_state_indices));

% 计算稳态误差
desired_value = reference0(end);  % 单位阶跃输入
steady_state_error = abs(desired_value - steady_state_value);

% 计算超调量 (Overshoot)
peak_value = max(position);
overshoot = max(0, (peak_value - desired_value) / max(abs(desired_value), eps) * 100);

% % 计算峰值时间 (Peak Time)
% [~, peak_index] = max(position);
% peak_time = time(peak_index)-0.5;

% 计算调整时间 (Settling Time)

upper = desired_value+0.005;
lower = desired_value-0.005;
tolerance = upper-lower;
if steady_state_error <= tolerance
    settling_time_index = find(position>upper | position < lower, 1,'last');
    if isempty(settling_time_index), settling_time = 0;
    else, settling_time = max(0, time(settling_time_index)-0.5); end
else
    settling_time = 0.5;
end

% % 计算振荡次数 (Number of Oscillations)
% zero_crossings = sum(diff(sign(position - desired_value)) ~= 0);
% num_oscillations = fix(zero_crossings / 2);

% 计算时间乘绝对误差 (ITAE)
% ITAE = trapz(time, time .* abs(position - reference1));
%计算RMSE
% rmse = sqrt(mean((position- reference1).^2));

if steady_state_error < 0 || steady_state_error >= 0.05 * reference1(end) || overshoot >= 20
    f(1)=inf;
    f(2)=inf;
    f(3)=inf;
    % f(4)=inf;
    % f(5)=inf;
    % f(6)=inf;
else
    f(1)=steady_state_error;
    f(2)=overshoot;
    % f(3)=peak_time;
    f(3)=settling_time;
    % f(5)=num_oscillations;
    % f(6)=rmse;
end