function [gb, g, gbest] = HPSO(N1, d, iterM, vref)
    clc; 
    %clear
    % 强制所有输入转为 double
    N1 = double(N1);
    d = double(d);
    iterM = double(iterM);
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
    
    
    
    
    % 目标函数，包含5个参数 + 5个误差项（k1~k5）
    f = @(pos) ...
        0.2 * sum(abs(-w0 .* pos(1) .* iq0 - ud0 - pos(6)))/length(uqx0) + ...
        0.2 * sum(abs((pos(3) .* iq0 + w0 .* pos(4)) - uq0 - pos(7)))/length(uqx0) + ...
        0.2 * sum(abs(pos(3) .* id1 - w0 .* pos(1) .* iq1 - ud1 - pos(8)))/length(uqx0) + ...
        0.2 * sum(abs(pos(3).* iq1 + w0 .* (pos(2) .* id1 + pos(4)) - uq1 - pos(9)))/length(uqx0) + ...
        0.2 * sum(abs(1.5*4.*pos(4) - pos(5).*w0/4 - tm0 - pos(10)))/length(uqx0);
    
    % N1 = 50; 
    % d = 10; 
    % iterM = 200;
    
    wmax = 0.9;
    wmin = 0.4; 
    c1 = 1.5; c2 = 1.5;
    
    % 辨识参量的范围tL
    t1L = [1.5e-4, 2.5e-4]; %Lq
    t2L = [1.5e-4, 2.5e-4]; %Ld
    t3L = [0.3, 0.4];       %R
    t4L = [0.006, 0.007];   %psi_f
    t5L = [5e-5,1e-4];      %B
    % 误差补偿项 范围
    t6L = [-2, 2];
    t7L = [-2, 2];
    t8L = [-2, 2];
    t9L = [-2, 2];
    t10L = [-2, 2];
    
    %辨识参量和误差补偿项的向量范围
    v1L = [-0.00001,0.00001];
    v2L = [-0.00001,0.00001];
    v3L = [-0.02, 0.02];
    v4L = [-0.003, 0.003];
    v5L = [-0.00001,0.00001];
    v6L = [-0.01, 0.01];
    v7L = [-0.01, 0.01];
    v8L = [-0.01, 0.01];
    v9L = [-0.01, 0.01];
    v10L = [-0.01, 0.01];
    
    v1 = v1L(1) + (v1L(2)-v1L(1))*rand(N1,1);
    v2 = v2L(1) + (v2L(2)-v2L(1))*rand(N1,1);
    v3 = v3L(1) + (v3L(2)-v3L(1))*rand(N1,1);
    v4 = v4L(1) + (v4L(2)-v4L(1))*rand(N1,1);
    v5 = v5L(1) + (v5L(2)-v5L(1))*rand(N1,1);
    v6 = v6L(1) + (v6L(2)-v6L(1))*rand(N1,1);
    v7 = v7L(1) + (v7L(2)-v7L(1))*rand(N1,1);
    v8 = v8L(1) + (v8L(2)-v8L(1))*rand(N1,1);
    v9 = v9L(1) + (v9L(2)-v9L(1))*rand(N1,1);
    v10 = v10L(1) + (v10L(2)-v10L(1))*rand(N1,1);
    %速度向量初始化
    v = [v1 v2 v3 v4 v5 v6 v7 v8 v9 v10];
    
    t1 = t1L(1) + (t1L(2)-t1L(1))*rand(N1,1);
    t2 = t2L(1) + (t2L(2)-t2L(1))*rand(N1,1);
    t3 = t3L(1) + (t3L(2)-t3L(1))*rand(N1,1);
    t4 = t4L(1) + (t4L(2)-t4L(1))*rand(N1,1);
    t5 = t5L(1) + (t5L(2)-t5L(1))*rand(N1,1);
    t6 = t6L(1) + (t6L(2)-t6L(1))*rand(N1,1);
    t7 = t7L(1) + (t7L(2)-t7L(1))*rand(N1,1);
    t8 = t8L(1) + (t8L(2)-t8L(1))*rand(N1,1);
    t9 = t9L(1) + (t9L(2)-t9L(1))*rand(N1,1);
    t10 = t10L(1) + (t10L(2)-t10L(1))*rand(N1,1);
    %位置向量初始化
    pop = [t1 t2 t3 t4 t5 t6 t7 t8 t9 t10];
    
    % 初始化粒子历史最优和全局最优
    pBV = ones(N1,1)*inf;
    gBV = ones(1,1)*inf;
    pBpos = pop;
    gBpos = ones(1,d);
    
    K = 3;
    neib = @(i) mod(i-1 + (0:i-1),N1) + 1;
    % gBV_record = zeros(iterM, 1);  % 存储每次迭代的全局最优值
    gBV_record=[];
    
    % 在循环之前添加数据文件初始化
    data_file = 'HPSO_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end
    
    for iter = 1:iterM
    
        
    
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
       
            local_ind = neib(i);
            [~,index] = min(pBV(local_ind));
            pLocal = pBpos(local_ind(index),:);
    
            omega = wmax - (wmax - wmin) * iter / iterM;
            q = rand;
            r1 = rand(1,d); r2 = rand(1,d); r3 = rand(1,d);
            
            v(i,:) = v(i,:) * omega + c1*r1.*(pBpos(i,:)-pop(i,:)) ...
                      + c2 * (q * r2 .* (gBpos - pop(i,:)) + (1 - q) * r3 .* (pLocal - pop(i,:)));
    
            pop(i,:) = pop(i,:) + v(i,:);
    
    
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
    
            if (pop(i,6) < t6L(1) || pop(i,6) > t6L(2))
                pop(i,6) = t6L(1) + (t6L(2) - t6L(1)) * rand;
            end
            if (pop(i,7) < t7L(1) || pop(i,7) > t7L(2))
                pop(i,7) = t7L(1) + (t7L(2) - t7L(1)) * rand;
            end
            if (pop(i,8) < t8L(1) || pop(i,8) > t8L(2))
                pop(i,8) = t8L(1) + (t8L(2) - t8L(1)) * rand;
            end
            if (pop(i,9) < t9L(1) || pop(i,9) > t9L(2))
                pop(i,9) = t9L(1) + (t9L(2) - t9L(1)) * rand;
            end
            if (pop(i,10) < t10L(1) || pop(i,10) > t10L(2))
                pop(i,10) = t10L(1) + (t10L(2) - t10L(1)) * rand;
            end
    
    
            % pop(i,j) 边界判断 ===
            if (pop(i,1) < t1L(1) || pop(i,1) > t1L(2))
                pop(i,1) = t1L(1) + (t1L(2) - t1L(1)) * rand;
            end
            if (pop(i,2) < t2L(1) || pop(i,2) > t2L(2))
                pop(i,2) = t2L(1) + (t2L(2) - t2L(1)) * rand;
            end
    
            if (pop(i,3) < t3L(1) || pop(i,3) > t3L(2))
                pop(i,3) = t3L(1) + (t3L(2) - t3L(1)) * rand;
            end
    
            if (pop(i,4) < t4L(1) || pop(i,4) > t4L(2))
                pop(i,4) = t4L(1) + (t4L(2) - t4L(1)) * rand;
            end
            if (pop(i,5) < t5L(1) || pop(i,5) > t5L(2))
                pop(i,5) = t5L(1) + (t5L(2) - t5L(1)) * rand;
            end
    
        end
    
        % gBV_record(iter) = gBV;         % 记录本次最优值
        gBV_record = [gBV_record;gBV];

        if mod(iter, 5) == 0 || iter == iterM
            save(data_file, 'gBV_record', 'iter', 'iterM');
        end

        gb=gBV_record;
        gbest=gBV;
        g=gBpos;
    
        % % 实时绘图
        % plot(gBV_record(1:iter), 'LineWidth', 2); 
        % xlabel('Iteration'); ylabel('Fitness (f)');
        % title('HPSO Optimization Progress');
        % grid on; drawnow;

        % 每5次迭代或最后一次迭代时保存数据

    end
    
    % ER =  ...
    %     abs(gBpos(1) - 2e-4)/gBpos(1) * 0.2 + ...
    %     abs(gBpos(2) - 2e-4)/gBpos(2) * 0.2 + ...
    %     abs(gBpos(3) - 0.36)/gBpos(3)* 0.2 + ...
    %     abs(gBpos(4) - 0.0064)/gBpos(4)* 0.2 + ...
    %     abs(gBpos(5) - 7.7062e-5)/gBpos(5) * 0.2 ...
    %     ;
    % 
    % 
    % fprintf ('optimal_value is %.3f\n', gBV);
    % fprintf('the corresponding position is %.8f, %.8f, %.8f, %.8f, %.8f\n', gBpos(1), gBpos(2), gBpos(3), gBpos(4),gBpos(5));
    % %fprintf('error is %.8f, %.8f, %.8f, %.8f, %.8f\n',gBpos(6), gBpos(7), gBpos(8), gBpos(9),gBpos(10))
    % fprintf('error range: %.6f\n %%', ER);
    % 
    % %save('result_HPSO.mat', 'gBV_record');

end
