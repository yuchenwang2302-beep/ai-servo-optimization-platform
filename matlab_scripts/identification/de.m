function [gb, g, gBV] = de(N, D, iterM, vref)
clc; % clear;
% vref=200;

% 强制所有输入转为 double
N = double(N);
D = double(D);
iterM = double(iterM);
vref = double(vref);

assignin('base', 'vref', vref); % 将 vref 设置到基础工作区

%% 数据提取 %%
sim('Spd_Discrete');
sim('Spd_Discrete2');

%%导入数据%%
%%ud%%
tud_0=simout_ud0.time;           % 时间向量，列向量
ud_0=simout_ud0.signals.values; % 对应信号值，列向量或矩阵
udx0 = find(tud_0 > 2 & tud_0 < 2.2);
tud0 = tud_0(udx0);
ud0 = ud_0(udx0);
tud_1=simout_ud1.time;           % 时间向量，列向量
ud_1=simout_ud1.signals.values; % 对应信号值，列向量或矩阵
udx1 = find(tud_1 > 2 & tud_1 < 2.2);
tud1 = tud_1(udx1);
ud1 = ud_1(udx1);
% fprintf('样本数ud0: %d\n', length(udx0));
% fprintf('样本数ud1: %d\n', length(udx1));
%%uq%%
tuq_0=simout_uq0.time;           % 时间向量，列向量
uq_0=simout_uq0.signals.values; % 对应信号值，列向量或矩阵
uqx0 = find(tuq_0 > 2 & tuq_0 < 2.2);
tqd0 = tuq_0(uqx0);
uq0 = uq_0(uqx0);
tuq_1=simout_uq1.time;           % 时间向量，列向量
uq_1=simout_uq1.signals.values; % 对应信号值，列向量或矩阵
uqx1 = find(tuq_1 > 2 & tuq_1 < 2.2);
tqd1 = tuq_1(uqx1);
uq1 = uq_1(uqx1);
% % 输出样本数
% fprintf('样本数uq0: %d\n', length(uqx0));
% fprintf('样本数uq1: %d\n', length(uqx1));
%%id%%
tid_0=simout_id0.time;
id_0=simout_id0.signals.values;
idx0 = find(tid_0 > 2 & tid_0 < 2.2);
tid0 = tid_0(idx0);
id0 = id_0(idx0);
tid_1=simout_id1.time;
id_1=simout_id1.signals.values;
idx1 = find(tid_1 > 2 & tid_1 < 2.2);
tid1 = tid_1(idx1);
id1 = id_1(idx1);
% % % 输出样本数
% fprintf('样本数id0: %d\n', length(idx0));
% fprintf('样本数id1: %d\n', length(idx1));

%%iq%%
tiq_0=simout_iq0.time;
iq_0=simout_iq0.signals.values;
iqx0 = find(tiq_0 >2 & tiq_0 < 2.2);
tiq0 = tiq_0(iqx0);
iq0 = iq_0(iqx0);
tiq_1=simout_iq1.time;
iq_1=simout_iq1.signals.values;
iqx1 = find(tiq_1 >2 & tiq_1 < 2.2);
tiq1 = tiq_1(iqx1);
iq1 = iq_1(iqx1);
% % 输出样本数
% fprintf('样本数iq0: %d\n', length(iqx0));
% fprintf('样本数iq1: %d\n', length(iqx1));
nn=length(iqx0);
%%w%%
tw=simout_w0.time;
w=simout_w0.signals.values;
wx0 = find(tw > 2 & tw < 2.2);
tw0 = tw(wx0);
w0 = w(wx0);

% % % 输出样本数
%  fprintf('样本数w0: %d\n', length(wx0));

%%TM%%
ttm=simout_Tm0.time;
tm=simout_Tm0.signals.values;
tmx = find(ttm > 2 & ttm <2.2);
ttm0 = ttm(tmx);
tm0 = tm(tmx);
% fprintf('2~3秒的样本数tm0: %d\n', length(tm0));
%%P%%
%p=4;

% 目标函数 %%
f = @(pos) ...
   0.2 * sum(abs(-w0 .* pos(1) .* iq0 - ud0-pos(6) * rand(nn,1)))/200000 + ...
    0.2 * sum(abs((pos(3) .* iq0 + w0 .* pos(4)) - uq0-pos(7) * rand(nn,1)))/200000 + ...
    0.2 * sum(abs(pos(3) .* id1 - w0 .* pos(1) .* iq1 - ud1-pos(8) * rand(length(iq1),1)))/200000 + ...
    0.2 * sum(abs(pos(3).* iq1 + w0 .* (pos(2) .* id1 + pos(4)) - uq1-pos(9) * rand(length(iq1),1)))/200000 + ...
    0.2 * sum(abs(1.5*4.*pos(4) - pos(5).*w0/4 - tm0-pos(10) * rand(length(w0),1)))/200000;
% %% 差分进化参数设置 %%
% N = 100;       % 种群规模
% D = 10;          % 参数维度
% T = 200;        % 最大迭代次数


F = 0.8;        % 差分因子
CR = 0.9;       % 交叉概率

lb = [1.5e-4, 1.5e-4, 0.3, 0.006, 5e-5, -5, -5, -5, -5, -5];
ub = [2.5e-4, 2.5e-4, 0.4, 0.007, 1e-4,  5,  5,  5,  5,  5];


%% 初始化种群 %%
F_ind = 0.5 + 0.3 * rand(N, 1);  % 每个个体的差分因子（范围 [0.5, 0.8]）
CR_ind = 0.9 * ones(N, 1);       % 每个个体的交叉概率（可稍高）

pop = repmat(lb, N, 1) + rand(N, D) .* (repmat(ub - lb, N, 1));
fitness = zeros(N, 1);
for i = 1:N
    fitness(i) = f(pop(i, :));
end

% gb = zeros(T, 1);
gBV_record = [];

% figure;
% hold on;
% h = plot(NaN, NaN, 'b-o', 'LineWidth', 1.5); % 空图初始化
% xlabel('迭代次数');
% ylabel('最优值');
% title('DE 收敛过程（每隔N代刷新）');
% grid on;
% refresh_interval = 5;  % 每隔5代刷新一次图像

% 在循环之前添加数据文件初始化
data_file = 'de_temp_data.mat';
if exist(data_file, 'file')
    delete(data_file);
end

%% 主循环 %%

for iter = 1:iterM
    for i = 1:N
        % jDE：以 0.1 概率更新个体 F 和 CR
if rand < 0.1
    F_ind(i) = 0.5 + 0.3 * randn;  % 正态扰动
    F_ind(i) = min(max(F_ind(i), 0.1), 1.0);  % 限制在 [0.1, 1.0]
end
if rand < 0.1
    CR_ind(i) = 0.5 + 0.1 * randn;
    CR_ind(i) = min(max(CR_ind(i), 0.0), 1.0);  % 限制在 [0, 1]
end

        % 随机选择 r1, r2, r3 (!= i)
        idx = randperm(N, 3);
        while any(idx == i)
            idx = randperm(N, 3);
        end
        r1 = idx(1); r2 = idx(2); r3 = idx(3);

        % 变异操作
vi = pop(r1,:) + F_ind(i) * (pop(r2,:) - pop(r3,:));
       % vi = max(min(vi, ub), lb);  % 保证在边界内
for j = 1:D
    if vi(j) < lb(j)
        vi(j) = lb(j) + rand * (lb(j) - vi(j));  % 反射回合法
    elseif vi(j) > ub(j)
        vi(j) = ub(j) - rand * (vi(j) - ub(j));
    end
end

        % 交叉操作
        g = pop(i,:);
        jrand = randi(D);
        for j = 1:D
            if rand < CR_ind(i) || j == jrand
                g(j) = vi(j);
            end
        end

        % 选择操作
        fit_ui = f(g);
        if fit_ui < fitness(i)
            pop(i,:) = g;
            fitness(i) = fit_ui;
        end
    end
% === 微扰机制（后期激活） ===
if iter > iterM * 0.6
    g = g + 0.01 * randn(1, D);  % 加入高斯噪声
    % 扰动后再次边界反射处理
    for j = 1:D
        if g(j) < lb(j)
            g(j) = lb(j) + rand * (lb(j) - g(j));
        elseif g(j) > ub(j)
            g(j) = ub(j) - rand * (g(j) - ub(j));
        end
    end
end

    [gBV, best_idx] = min(fitness);
    gBV_record = [gBV_record;gBV];
    gb = gBV_record;
    
    % % 每隔 refresh_interval 代更新图像（或首代和末代）
    % if mod(gen, refresh_interval) == 0 || gen == 1 || gen == T
    %     set(h, 'XData', 1:gen, 'YData', gb(1:gen));
    %     drawnow;  % 刷新图像显示
    %      pause(0.01); 
    % end

    % 每5次迭代或最后一次迭代时保存数据
    if mod(iter, 5) == 0 || iter == iterM
        save(data_file, 'gBV_record', 'iter', 'iterM');
    end

    % fprintf('第 %d 代 最优值 = %.6f\n', gen, gBV);


end
 
% %% 输出最优结果 %%
% best_solution = pop(best_idx,:);
% fprintf('\n最终最优值为：%.6f\n', gb(end));
% fprintf('最优参数为：\nLq = %.6g H\nLd = %.6g H\nR = %.4f Ohm\nψf = %.5f Wb\nB = %.6g Nms/rad\n', ...
%     best_solution(1), best_solution(2), best_solution(3), best_solution(4), best_solution(5));
% fprintf('扰动因子 k1~k5 = %.2f, %.2f, %.2f, %.2f, %.2f\n', ...
%     best_solution(6), best_solution(7), best_solution(8), best_solution(9), best_solution(10));
% toterror2= 0.2*abs((best_solution(1)-2e-4)/best_solution(1))+0.2*abs((best_solution(2)-2e-4)/best_solution(2))+...
%     0.2*abs((best_solution(3)-0.36)/best_solution(3))+0.2*abs((best_solution(4)-0.0064)/best_solution(4))+0.2*abs((best_solution(5)-7.7062e-5)/best_solution(5));
% fprintf('最终五个参数误差比例和%.6f',toterror2);
% %% 可视化收敛 %%
% figure;
% plot(1:T, gb, 'LineWidth', 2);
% xlabel('迭代次数'); ylabel('最优值');
% title('差分进化（DE）收敛曲线'); grid on;
% % 保存当前算法的收敛数据
% save('best_history_de.mat', 'gb');         % 保存最优值记录
    