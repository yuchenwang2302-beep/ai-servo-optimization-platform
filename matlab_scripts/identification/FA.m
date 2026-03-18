function [gb, g, gbest] = FA(N, d, iterM, vref)

clc
% clear
% vref=3200;

% 强制所有输入转为 double
N = double(N);
d = double(d);
iterM = double(iterM);
vref = double(vref);

assignin('base', 'vref', vref); % 将 vref 设置到基础工作区

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
fprintf('样本数uq0: %d\n', length(uqx0));
fprintf('样本数uq1: %d\n', length(uqx1));
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
% % 输出样本数
fprintf('样本数id0: %d\n', length(idx0));
fprintf('样本数id1: %d\n', length(idx1));
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
fprintf('样本数iq0: %d\n', length(iqx0));
fprintf('样本数iq1: %d\n', length(iqx1));
nn=length(iqx0);
%%w%%
tw=simout_w0.time;
w=simout_w0.signals.values;
wx0 = find(tw > 2 & tw < 2.2);
tw0 = tw(wx0);
w0 = w(wx0);

% % 输出样本数
 fprintf('样本数w0: %d\n', length(wx0));

%%TM%%
ttm=simout_Tm0.time;
tm=simout_Tm0.signals.values;
tmx = find(ttm > 2 & ttm <2.2);
ttm0 = ttm(tmx);
tm0 = tm(tmx);
fprintf('2~3秒的样本数tm0: %d\n', length(tm0));
%%P%%
%p=4;



%------------------------------------------------------------上面为读取smk数据


%% 定义目标函数（增加误差项 pos(6:10)）
f = @(pos) ...
    0.2 * sum(abs(-w0 .* pos(1) .* iq0 - ud0 - pos(6))) / length(iq0) + ...
    0.2 * sum(abs((pos(3) .* iq0 + w0 .* pos(4)) - uq0 - pos(7))) / length(iq0) + ...
    0.2 * sum(abs(pos(3) .* id1 - w0 .* pos(1) .* iq1 - ud1 - pos(8))) / length(iq0) + ...
    0.2 * sum(abs(pos(3).* iq1 + w0 .* (pos(2) .* id1 + pos(4)) - uq1 - pos(9))) / length(iq0) + ...
    0.2 * sum(abs(1.5*4.*pos(4) - pos(5).*w0/4 - tm0 - pos(10))) / length(iq0);

%% 初始化
% N = 50;          % 萤火虫数量
% iterM = 200;       % 最大迭代次数
% d = 10;          % 参数个数（5物理 + 5误差）
gamma = 1;       % 光吸收
beta0 = 2;       % 初始吸引强度
alpha = 0.1;     % 随机移动步长

% 参数边界
tL = [1.5e-4 2.5e-4;  % Lq
          1.5e-4 2.5e-4;  % Ld
          0.3    0.4;     % R
          0.006  0.007;   % psi_f
          5e-5   1e-4;    % B
         -2      2;       % k1 此处往下是误差补偿项
         -2      2;       % k2
         -2      2;       % k3
         -2      2;       % k4
         -2      2];      % k5

% 初始化种群
pop = rand(N,d) .* (tL(:,2)' - tL(:,1)') + tL(:,1)';
% gBV_record = zeros(iterM, 1);  % 存储每次迭代的全局最优值
gBV_record = [];

%% 初始化
fitness = zeros(N,1);
for i = 1:N
    fitness(i) = f(pop(i,:));
end


% 在循环之前添加数据文件初始化
data_file = 'FA_temp_data.mat';
if exist(data_file, 'file')
    delete(data_file);
end

for iter = 1:iterM
    for i = 1:N
        for j = 1:N
            if fitness(j) < fitness(i)
                r    = norm(pop(i,:) - pop(j,:));
                beta = beta0 * exp(-gamma * r^2);
                pop(i,:) = pop(i,:) + beta*(pop(j,:)-pop(i,:)) ...
                                   + alpha*(rand(1,d)-0.5);
                % 越界修剪
                pop(i,:) = max(min(pop(i,:),tL(:,2)'), tL(:,1)');
                fitness(i) = f(pop(i,:));   % 更新适应度
            end
        end
    end
    
    %
    gBV_record = [gBV_record;min(fitness)];     


    % plot(gBV_record(1:iter),'LineWidth',2);
    % xlabel('Iteration'); ylabel('Fitness (f)');
    % title('FA Optimization Progress'); grid on; drawnow;
    
    % 可以注释掉这个
    alpha = alpha * 0.97;

    % 每5次迭代或最后一次迭代时保存数据
    if mod(iter, 5) == 0 || iter == iterM
        save(data_file, 'gBV_record', 'iter', 'iterM');
    end

    gBpos = pop(i,:);

    gb=gBV_record;
    gbest=min(fitness);
    g=gBpos;
end



% %% 输出结果
% % [bestfit, idx] = min(fitness);
% gBpos = pop(idx,:);
% fprintf('optimal value: %.6f\n', bestfit);
% fprintf('corresponding position: Lq=%.8f, Ld=%.8f, R=%.8f, ψf=%.8f, B=%.8f\n', gBpos(1), gBpos(2), gBpos(3), gBpos(4), gBpos(5));
% %fprintf('误差补偿项: k1=%.4f, k2=%.4f, k3=%.4f, k4=%.4f, k5=%.4f\n', gBpos(6), gBpos(7), gBpos(8), gBpos(9), gBpos(10));

% %% 误差率计算（仍基于前5个物理量）
% ER =  ...
%     abs(gBpos(1) - 2e-4)/gBpos(1) * 0.2 + ...
%     abs(gBpos(2) - 2e-4)/gBpos(2) * 0.2 + ...
%     abs(gBpos(3) - 0.36)/gBpos(3) * 0.2 + ...
%     abs(gBpos(4) - 0.0064)/gBpos(4) * 0.2 + ...
%     abs(gBpos(5) - 7.7062e-5)/gBpos(5) * 0.2 ;
% 
% fprintf('误差率 ER = %.6f  \n', ER);

%save('result_FA_3200.mat','record_gBV2');