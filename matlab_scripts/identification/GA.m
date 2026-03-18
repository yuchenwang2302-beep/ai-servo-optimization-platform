function [gb, g, gbest] = GA(popsize, dimension, iterM, vref)
    clc; 
    %clear;
    vref=vref;

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
    
    
    
    % popsize = 40;%优化的参数组数量（gene组）
    
    tL = [1.5e-4 2.5e-4;   % Lq
          1.5e-4 2.5e-4;   % Ld
          0.3     0.4;     % R
          0.006   0.007;   % ψ_f
          5e-5    1e-4;    % B
         -2       2;       % k1
         -2       2;       % k2
         -2       2;       % k3
         -2       2;       % k4
         -2       2];      % k5
    
    bit_length = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10];
    Gelength = sum(bit_length);
    % dimension = 10;
    
    p_cr = 0.8;%交叉互换概率
    p_mut = 0.1;%突变概率
    
    % iterM = 200;
    
    optimal_value = rand*inf;
    BVpos = ones(1,dimension);
    
    pop = round(rand(popsize,Gelength)); %pop 二进制
    pop1 = ones(popsize, Gelength);
    
    % gBV_record = zeros(iterM, 1); %record optimal value per cycle
    gBV_record=[];

    % 在循环之前添加数据文件初始化
    data_file = 'GA_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end
    
    for iter = 1:iterM
    
        % 适应度
        pow2   = 2.^(9:-1:0);
        temp   = zeros(popsize, dimension);
        pop2   = zeros(popsize, dimension);
    
        for k = 1:dimension
            seg        = pop(:,10*(k-1)+1:10*k);     % 1-10,11-20,21-30,31-40.....
            temp(:,k)  = seg * pow2';                % 二进制转十进制
            pop2(:,k)  = tL(k,1) + temp(:,k) * (tL(k,2)-tL(k,1))/1023;
        end
    
        fitvalue = zeros(popsize,1);
        for b = 1:popsize
            fitvalue(b) = ...
                0.2*mean(abs(-w0 .* pop2(b,1) .* iq0                       - ud0 - pop2(b,6))) + ...
                0.2*mean(abs( pop2(b,3) .* iq0 + w0 .* pop2(b,4)           - uq0 - pop2(b,7))) + ...
                0.2*mean(abs( pop2(b,3).* id1 - w0 .* pop2(b,1) .* iq1     - ud1 - pop2(b,8))) + ...
                0.2*mean(abs( pop2(b,3).* iq1 + w0.*(pop2(b,2).*id1+pop2(b,4)) - uq1 - pop2(b,9))) + ...
                0.2*mean(abs(1.5*4*pop2(b,4) - pop2(b,5).*w0/4 - tm0 - pop2(b,10)));
        end
    
        %优质选择
        [bestFit, idxBest] = min(fitvalue);   % 我们要找越小值越优
        eliteChrom         = pop(idxBest,:);  
    
        %轮盘赌选择,和demo不同,这里需要优化最小值,所以是需要最小值对应的参数,别用fiv/sumfiv,那个淘汰了最小值
        ticket = 1./(fitvalue + eps);                 % eps是限制防止除了个0
        cdf    = cumsum(ticket) / sum(ticket);        % 累积分布
    
        newpop = zeros(size(pop));                    % 预
        for m = 1:popsize
            r           = rand;
            selIdx      = find(cdf >= r, 1, 'first');
            newpop(m,:) = pop(selIdx,:);
        end
    
        %cross rate
        newpop2 = newpop;                    
        for i = 1:2:popsize-1
            if rand < p_cr
                point = randi([1, size(pop,2)-1]);    % 至少留 1 bit
                newpop2(i,  :) = [newpop(i,1:point)   , newpop(i+1,point+1:end)];
                newpop2(i+1,:) = [newpop(i+1,1:point) , newpop(i  ,point+1:end)];
            end
        end
    
        % mut rate
        newpop3 = newpop2;
        mutMask = rand(size(newpop3)) < p_mut;
        newpop3(mutMask) = 1 - newpop3(mutMask);      % 0↔1 翻转
    
        %优质gene(目标点)更新
        pop            = newpop3;
        pop(1,:)       = eliteChrom;                  % 优质基因(配套参数)占第 1 行
    
        %Plotting
        if bestFit < optimal_value
            optimal_value = bestFit;
            BVpos         = pop2(idxBest,:);          % 
        end
        gBV_record=[gBV_record;optimal_value];
    
        % plot(gBV_record(1:iter),'LineWidth',2); grid on;
        % xlabel('Iteration'); ylabel('Best fitness');
        % title('GA Optimization Progress'); drawnow;

        gb=gBV_record;
        gbest=optimal_value;
        g=BVpos;
        
         % 每5次迭代或最后一次迭代时保存数据
        if mod(iter, 5) == 0 || iter == iterM
            save(data_file, 'gBV_record', 'iter', 'iterM');
        end
    end
    
    % ER =  ...
    %     abs(BVpos(1) - 2e-4)/BVpos(1) * 0.2 + ...
    %     abs(BVpos(2) - 2e-4)/BVpos(2) * 0.2 + ...
    %     abs(BVpos(3) - 0.36)/BVpos(3) * 0.2 + ...
    %     abs(BVpos(4) - 0.0064)/BVpos(4) * 0.2 + ...
    %     abs(BVpos(5) - 7.7062e-5)/BVpos(5) * 0.2 ;
    % 
    % fprintf ('optimal_value is %.3f\n', optimal_value);
    % fprintf('the corresponding position is %.8f, %.8f, %.8f, %.8f, %.8f\n', BVpos(1), BVpos(2), BVpos(3), BVpos(4),BVpos(5));
    % %fprintf('error is %.8f, %.8f, %.8f, %.8f, %.8f\n',BVpos(6), BVpos(7), BVpos(8), BVpos(9), BVpos(10))
    % fprintf('error is : %.6f \n',ER);
    % 
    % %save('result_GA_.mat', 'gBV_record');