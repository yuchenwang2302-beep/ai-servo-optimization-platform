function [gb, g, gbest] = pso2(N, D, T, vref)
clc
%clear
% 强制所有输入转为 double
N = double(N);
D = double(D);
T = double(T);
vref = double(vref);
% vref=vref


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
% % 输出样本数
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

% % 输出样本数
% fprintf('样本数w0: %d\n', length(wx0));

%%TM%%
ttm=simout_Tm0.time;
tm=simout_Tm0.signals.values;
tmx = find(ttm > 2 & ttm <2.2);
ttm0 = ttm(tmx);
tm0 = tm(tmx);
% fprintf('2~3秒的样本数tm0: %d\n', length(tm0));
%%P%%
%p=4;



%Lq,Ld,R,psi_f
%iq0 iq1 id1
%ud0 uq0 ud1 uq1 待输入

% f = @(pos) ...
%     0.2 * sum(abs(-w0 .* pos(1) .* iq0 - ud0))/length(uqx0) + ...
%     0.2 * sum(abs((pos(3) .* iq0 + w0 .* pos(4)) - uq0))/length(uqx0) + ...
%     0.2 * sum(abs(pos(3) .* id1 - w0 .* pos(1) .* iq1 - ud1))/length(uqx0) + ...
%     0.2 * sum(abs(pos(3).* iq1 + w0 .* (pos(2) .* id1 + pos(4)) - uq1))/length(uqx0) + ...
%     0.2 * sum(abs(1.5*4.*pos(4) - pos(5).*w0/4 - tm0))/length(uqx0);
f = @(pos) ...
    0.2 * sum(abs(-w0 .* pos(1) .* iq0 - ud0 -pos(6)*ones(nn,1)*rand))/nn + ...
    0.2 * sum(abs((pos(3) .* iq0 + w0 .* pos(4)) - uq0 - pos(7)*ones(nn,1)*rand))/nn + ...
    0.2 * sum(abs(pos(3) .* id1 - w0 .* pos(1) .* iq1 - ud1 - pos(8)*ones(nn,1)*rand))/nn + ...
    0.2 * sum(abs(pos(3).* iq1 + w0 .* (pos(2) .* id1 + pos(4)) - uq1 - pos(9)*ones(nn,1)*rand))/nn + ...
    0.2 * sum(abs(1.5*4.*pos(4) - pos(5).*w0/4 - tm0 - pos(10)*ones(nn,1)*rand))/nn;



N1 = N;
d = D;
interM = T;

c1 = 1.5;
c2 = 1.5;
omega_max = 0.9;
omega_min = 0.4;

t1L = [1.5e-4, 2.5e-4]; %Lq轴电感范围
t2L = [1.5e-4, 2.5e-4]; %Ld轴电感范围
t3L = [0.3, 0.4];       %电阻范围
t4L = [0.006, 0.007];   %磁链范围
t5L = [5e-5,1e-4];            %转动惯量范围
% t1L = [0, 0.1]; %Lq
% t2L = [0, 0.1]; %Ld
% t3L = [0, 1];       %R
% t4L = [0, 0.2];   %psi_f
% t5L = [0,0.1];      %B

% 原前五项边界不变
t6L = [-5, 5];  % k1
t7L = [-5, 5];  % k2
t8L = [-5, 5];  % k3
t9L = [-5, 5];  % k4
t10L = [-5, 5]; % k5




v1L = [-0.00001,0.00001];
v2L = [-0.00001,0.00001];
v3L = [-0.02, 0.02];
v4L = [-0.003, 0.003];
v5L = [-0.00001,0.00001];
v6L = [-0.1, 0.2];
v7L = [-0.1, 0.2];
v8L = [-0.1, 0.2];
v9L = [-0.1, 0.2];
v10L = [-0.1, 0.2];




v1 = v1L(1) + (v1L(2)-v1L(1))*rand(N1,1);
v2 = v2L(1) + (v2L(2)-v2L(1))*rand(N1,1);
v3 = v3L(1) + (v3L(2)-v3L(1))*rand(N1,1);
v4 = v4L(1) + (v4L(2)-v4L(1))*rand(N1,1);
v5 = v5L(1) + (v5L(2)-v5L(1))*rand(N1,1);
v6 = -0.1 + 0.2 * rand(N1,1);
v7 = -0.1 + 0.2 * rand(N1,1);
v8 = -0.1 + 0.2 * rand(N1,1);
v9 = -0.1 + 0.2 * rand(N1,1);
v10 = -0.1 + 0.2 * rand(N1,1);



t1 = t1L(1) + (t1L(2)-t1L(1))*rand(N1,1);
t2 = t2L(1) + (t2L(2)-t2L(1))*rand(N1,1);
t3 = t3L(1) + (t3L(2)-t3L(1))*rand(N1,1);
t4 = t4L(1) + (t4L(2)-t4L(1))*rand(N1,1);
t5 = t5L(1) + (t5L(2)-t5L(1))*rand(N1,1);
t6 = t6L(1) + (t6L(2) - t6L(1)) * rand(N1,1);
t7 = t7L(1) + (t7L(2) - t7L(1)) * rand(N1,1);
t8 = t8L(1) + (t8L(2) - t8L(1)) * rand(N1,1);
t9 = t9L(1) + (t9L(2) - t9L(1)) * rand(N1,1);
t10 = t10L(1) + (t10L(2) - t10L(1)) * rand(N1,1);

v = [v1 v2 v3 v4 v5 v6 v7 v8 v9 v10];
pop = [t1 t2 t3 t4 t5 t6 t7 t8 t9 t10];
% v = [v1 v2 v3 v4 v5];
% pop = [t1 t2 t3 t4 t5];
pBV = ones(N1,1)*inf;
gBV = ones(1,1)*inf;
pBpos = pop;
gBpos = ones(1,d);
% 在 for 循环之前初始化
% gBV_record = zeros(interM, 1);  % 用于保存每一代的全局最优值
gBV_record=[];
% % 初始化动态绘图
% figure;
% hold on;
% h = plot(NaN, NaN, 'b-o', 'LineWidth', 1.5);  % 空图像对象，用于后续更新
% xlabel('Iteration');
% ylabel('Best Fitness Value');
% title('PSO Iteration Progress (Updated every N iterations)');
% grid on;
% refresh_interval = 5;  % 每隔多少代刷新一次图像

% 在循环之前添加数据文件初始化
data_file = 'pso_temp_data.mat';
if exist(data_file, 'file')
    delete(data_file);
end

for iter = 1:interM
    f_value = zeros(N1, 1);

    for i = 1:N1
        f_value(i) = f(pop(i,:));
    end

    for i = 1:N1
        if f_value(i) < pBV(i)
            pBV(i,:) = f_value(i);
            pBpos(i,:) = pop(i,:);
        end
        if pBV(i)<gBV
            gBV = pBV(i);
            gBpos = pop(i,:);
        end

        r1 = rand(1,d);
        r2 = rand(1,d);
        omega = omega_max - (omega_max-omega_min)*i/interM;%N1;
        % v(i,:) = v(i,:) * omega + c1*r1.*(pBpos(i,:)-pop(i,:)) + c2*r2.*(gBpos - pop(i,:));
        v(i,:) = double(v(i,:)) * omega + c1 * r1 .* (pBpos(i,:) - pop(i,:)) + c2 * r2 .* (gBpos - pop(i,:));
        pop(i,:) = abs(pop(i,:)+v(i,:));
        %

        if (v(i,1) <= v1L(1) || v(i,1) >= v1L(2))
            v(i,1) = v1L(1) + (v1L(2) - v1L(1)) * rand;
        end
        if (v(i,2) <= v2L(1) || v(i,2) >= v2L(2))
            v(i,2) = v2L(1) + (v2L(2) - v2L(1)) * rand;
        end
        if (v(i,3) <= v3L(1) || v(i,3) >= v3L(2))
            v(i,3) = v3L(1) + (v3L(2) - v3L(1)) * rand;
        end
        if (v(i,4) <= v4L(1) || v(i,4) >= v4L(2))
            v(i,4) = v4L(1) + (v4L(2) - v4L(1)) * rand;
        end
        if (v(i,5) <= v5L(1) || v(i,5) >= v5L(2))
            v(i,5) = v5L(1) + (v5L(2) - v5L(1)) * rand;
        end
        if (v(i,6) <= v6L(1) || v(i,6) >= v6L(2))
            v(i,6) = v6L(1) + (v6L(2) - v6L(1)) * rand;
        end
        if (v(i,7) <= v7L(1) || v(i,7) >= v7L(2))
            v(i,7) = v7L(1) + (v7L(2) - v7L(1)) * rand;
        end
        if (v(i,8) <= v8L(1) || v(i,8) >= v8L(2))
            v(i,8) = v8L(1) + (v8L(2) - v8L(1)) * rand;
        end
        if (v(i,9) <= v9L(1) || v(i,9) >= v9L(2))
            v(i,9) = v9L(1) + (v9L(2) - v9L(1)) * rand;
        end
        if (v(i,10) <= v10L(1) || v(i,10) >= v10L(2))
            v(i,10) = v10L(1) + (v10L(2) - v10L(1)) * rand;
        end




        % pop(i,j) 边界判断 ===
        if (pop(i,1) <= t1L(1) || pop(i,1) >= t1L(2))
            pop(i,1) = t1L(1) + (t1L(2) - t1L(1)) * rand;
        end
        if (pop(i,2) <= t2L(1) || pop(i,2) >= t2L(2))
            pop(i,2) = t2L(1) + (t2L(2) - t2L(1)) * rand;
        end
        if (pop(i,3) <= t3L(1) || pop(i,3) >= t3L(2))
            pop(i,3) = t3L(1) + (t3L(2) - t3L(1)) * rand;
        end
        if (pop(i,4) <= t4L(1) || pop(i,4) >= t4L(2))
            pop(i,4) = t4L(1) + (t4L(2) - t4L(1)) * rand;
        end
        if (pop(i,5) <= t5L(1) || pop(i,5) >= t5L(2))
            pop(i,5) = t5L(1) + (t5L(2) - t5L(1)) * rand;
        end
        if (pop(i,6) <= t6L(1) || pop(i,6) >= t6L(2))
            pop(i,6) = t6L(1) + (t6L(2) - t6L(1)) * rand;
        end
        if (pop(i,7) <= t7L(1) || pop(i,7) >= t7L(2))
            pop(i,7) = t7L(1) + (t7L(2) - t7L(1)) * rand;
        end
        if (pop(i,8) <= t8L(1) || pop(i,8) >= t8L(2))
            pop(i,8) = t8L(1) + (t8L(2) - t8L(1)) * rand;
        end
        if (pop(i,9) <= t9L(1) || pop(i,9) >= t9L(2))
            pop(i,9) = t9L(1) + (t9L(2) - t9L(1)) * rand;
        end
        if (pop(i,10) <= t10L(1) || pop(i,10) >= t10L(2))
            pop(i,10) = t10L(1) + (t10L(2) - t10L(1)) * rand;
        end

        % % 每5次迭代或最后一次迭代时保存数据
        % if mod(iter, 5) == 0 || iter == interM
        %     save(data_file, 'gBV_record', 'iter', 'interM');
        % end
    end
    % gBV_record(iter) = gBV;  % 记录当前迭代的最优目标函数值
    
    % 每5次迭代或最后一次迭代时保存数据
    if mod(iter, 5) == 0 || iter == interM
        save(data_file, 'gBV_record', 'iter', 'interM');
    end
    
    gBV_record=[gBV_record;gBV];
    % 保存每一代的全局最优值

    % % 每10次迭代或最后一次迭代时保存数据
    %   if mod(iter, 10) == 0 || iter == interM
    %       save(pso_data_file, 'gBV_record', 'iter', 'interM');
    %   end

    % % 每隔 refresh_interval 代刷新一次图像
    % if mod(iter, refresh_interval) == 0 || iter == 1 || iter == interM
    %     set(h, 'XData', 1:iter, 'YData', gBV_record(1:iter));
    %     drawnow;  % 刷新图像显示
    %      pause(0.01);
    % end

    gb=gBV_record;
    gbest=gBV;
    g=gBpos

    % % 保存结果到 .mat 文件
    % save('pso_results.mat', 'gb');

end

% fprintf ('optimal_value is %.3f\n', gBV);
% fprintf('the corresponding position is %.6f, %.6f, %.6f, %.6f, %.6f\n', gBpos(1), gBpos(2), gBpos(3), gBpos(4),gBpos(5));
% fprintf('the corresponding position is %.6f, %.6f, %.6f, %.6f, %.6f\n', gBpos(6), gBpos(7), gBpos(8), gBpos(9),gBpos(10));
% fprintf('percentage is %.6f, %.6f, %.6f, %.6f, %.6f\n', (gBpos(1)-2e-4)/gBpos(1),(gBpos(2)-2e-4)/gBpos(2),(gBpos(3)-0.36)/gBpos(3), (gBpos(4)-0.0064)/gBpos(4),(gBpos(5)-7.7062e-5)/gBpos(5));
% tot=0.2*abs((gBpos(1)-2e-4)/gBpos(1))+0.2*abs((gBpos(2)-2e-4)/gBpos(2))+0.2*abs((gBpos(3)-0.36)/gBpos(3))+...
% 0.2*abs((gBpos(4)-0.0064)/gBpos(4))+0.2*abs((gBpos(5)-7.7062e-5)/gBpos(5));
% fprintf('final error%.6f',tot);
% figure;
% plot(1:interM, gBV_record, 'b-o', 'LineWidth', 1.5);
% xlabel('Iteration');
% ylabel('Best Fitness Value');
% title('PSO Iteration Progress');
% grid on;
% save('gBV_record_data.mat', 'gBV_record');