function [gb, g, gbest] = ia(NP, D, iterM, vref)
    clc; 
    %clear
    % 强制所有输入转为 double
    NP = double(NP);
    D = double(D);
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
    
    % D = 10;          % 参数维度
    % NP = 100;        % 个体数量
    Xs = 1;          % 上限比例（实际边界用单独向量控制）
    Xx = 0;          % 下限比例
    % G = 200;         % 最大代数
    pm = 0.7;        % 变异概率
    alfa = 1;        % 激励度系数
    belta = 1;       % 激励度系数
    detas = 0.1;     % 相似度阈值
    Ncl = 10;        % 克隆个体数
    deta0 = 0.5;     % 初始变异强度
    
    f = @(pos) ...
        0.2 * sum(abs(-w0 .* pos(1) .* iq0 - ud0 - pos(6)*rand(nn,1)))/nn + ...
        0.2 * sum(abs((pos(3) .* iq0 + w0 .* pos(4)) - uq0 - pos(7)*rand(nn,1)))/nn + ...
        0.2 * sum(abs(pos(3).*id1 - w0.*pos(1).*iq1 - ud1 - pos(8)*rand(nn,1)))/nn + ...
        0.2 * sum(abs(pos(3).*iq1 + w0.*(pos(2).*id1 + pos(4)) - uq1 - pos(9)*rand(nn,1)))/nn + ...
        0.2 * sum(abs(1.5*4.*pos(4) - pos(5).*w0/4 - tm0 - pos(10)*rand(nn,1)))/nn;
    
    tL = [1.5e-4, 2.5e-4;
          1.5e-4, 2.5e-4;
          0.3,    0.4;
          0.006,  0.007;
          5e-5,   1e-4;
         -5,      5;
         -5,      5;
         -5,      5;
         -5,      5;
         -5,      5];
    
    %% 初始种群
    pop = zeros(D, NP);
    for i = 1:D
        pop(i,:) = tL(i,1) + (tL(i,2)-tL(i,1)) * rand(1, NP);
    end
    
    %% 初始适应度（亲和度 = -目标值）
    for np = 1:NP
        aff(np) = -f(pop(:,np));
    end
    
    % 在循环之前添加数据文件初始化
    data_file = 'ia_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end

    %% 主迭代
    % gBV_record = zeros(G,1);
    gBV_record = [];
    for iter = 1:iterM
        %% 计算浓度因子
        for np = 1:NP
            for j = 1:NP
                dist(j) = norm(pop(:,np) - pop(:,j));
                similarity(j) = dist(j) < detas;
            end
            ND(np) = sum(similarity)/NP;
        end
    
        score = alfa * aff - belta * ND;
        [~, idx] = sort(score, 'descend');
        elite = pop(:, idx(1:NP/2));
    
        %% 克隆与变异
        offspring = [];
        for i = 1:NP/2
            a = elite(:,i);
            clones = repmat(a, 1, Ncl);
            deta = deta0 / (iter + 1);
            for j = 2:Ncl
                for d = 1:D
                    if rand < pm
                        clones(d,j) = clones(d,j) + (rand-0.5) * deta;
                    end
                    % 边界控制
                    if clones(d,j) < tL(d,1)
                        clones(d,j) = tL(d,1) + rand * (tL(d,2)-tL(d,1));
                    elseif clones(d,j) > tL(d,2)
                        clones(d,j) = tL(d,2) - rand * (tL(d,2)-tL(d,1));
                    end
                end
            end
            % 克隆抑制：取最优一个
            for j = 1:Ncl
                caff(j) = -f(clones(:,j));
            end
            [~, bestIdx] = max(caff);
            offspring = [offspring clones(:,bestIdx)];
            aff_new(i) = caff(bestIdx);
        end
    
        %% 补充新个体
        newpop = zeros(D, NP/2);
        for i = 1:D
            newpop(i,:) = tL(i,1) + (tL(i,2)-tL(i,1)) * rand(1, NP/2);
        end
        for i = 1:NP/2
            aff_rnd(i) = -f(newpop(:,i));
        end
    
        %% 合并 + 选前 NP 个
        pop_all = [offspring newpop];
        aff_all = [aff_new aff_rnd];
        for i = 1:NP
            for j = 1:NP
                d2(j) = norm(pop_all(:,i) - pop_all(:,j));
                sim2(j) = d2(j) < detas;
            end
            ND_all(i) = sum(sim2)/NP;
        end
        score_all = alfa * aff_all - belta * ND_all;
        [~, idx] = sort(score_all, 'descend');
        pop = pop_all(:, idx(1:NP));
        aff = aff_all(idx(1:NP));
    
        %% 记录最优值
        best_pos = pop(:,1);
        % gBV_record(gen) = -aff(1);
        gBV_record = [gBV_record,-aff(1)];

         % 每5次迭代或最后一次迭代时保存数据
        if mod(iter, 5) == 0 || iter == iterM
            save(data_file, 'gBV_record', 'iter', 'iterM');
        end

        gb=gBV_record
        gbest=gBV_record(end)
        g=best_pos

    
    %     % 可视化
    % if mod(gen,5)==0 || gen==1
    %     fprintf("Gen %d, Best = %.6f\n", gen, gBV_record(gen));
    % 
    %     figure(1); clf;
    %     plot(gBV_record(1:gen), 'b-o');
    %     xlabel('Iteration'); ylabel('Best Fitness');
    %     title(['免疫算法收敛过程 - 第 ' num2str(gen) ' 代']);
    %     drawnow;  % 实时刷新图像
    end
    
    end
    
    
    % %% 输出结果
    % figure; plot(gBV_record, 'b-o');
    % xlabel('Iteration'); ylabel('Best Fitness');
    % title('免疫算法迭代收敛曲线');
    % 
    % fprintf('最优值：%.6f\n', gBV_record(end));
    % fprintf('最优参数：\n');
    % disp(best_pos');
    % %% 真实值
    % true_val = [2e-4, 2e-4, 0.36, 0.0064, 7.7062e-5];
    % 
    % %% 提取前5个最优参数
    % best_five = best_pos(1:5)';
    % 
    % %% 归一化误差计算
    % error_ratio = abs(best_five - true_val) ./ true_val;
    % 
    % %% 显示结果
    % fprintf('前五个最优参数：\n');
    % disp(best_five);
    % final_error = sum(0.2 * error_ratio);
    % fprintf('与真实值 [1, 2, 3, 4, 5] 的归一化误差：\n');
    % disp(error_ratio);
    % fprintf('五项综合归一化误差 final_error = %.6f\n', final_error);
    % 
    % save('gBV_record_result.mat', 'gBV_record');  % 保存收敛曲线



    