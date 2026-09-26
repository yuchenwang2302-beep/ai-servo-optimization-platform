function [gBV, gBpos, time, reference0, position] = GA_optimization(N, d, iterM, objective)
    if nargin < 4, objective = 'ITSE'; end
    clc; % clear;
    % vref = 3200;
    T = 0.5;
    % d = 11;
    % popsize = 50;
    % iterM = 50;

    % 强制所有输入转为 double
    N = double(N);
    d = double(d);
    iterM = double(iterM);
    
    % 参数边界
    [lb, ub] = servo_search_bounds('standard');
    
    bit_length = 10;
    total_bits = d * bit_length;
    p_cr = 0.8;
    p_mut = 0.1;
    
    f = @(x) fun_position(x, T, objective);
    pop = randi([0,1], N, total_bits);
    
    gBV = inf;
    gBpos = zeros(1, d);
    % gBV_record = zeros(iterM, 1);
    gBV_record = [];

    % % 在循环之前添加数据文件初始化
    % data_file1 = fullfile(output_dir, 'ga_temp_data1.mat');  % 使用 fullfile 确保路径正确
    % if exist(data_file1, 'file')
    %     delete(data_file1);
    % end

    % 在循环之前添加数据文件初始化
    data_file = 'ga_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end
    
    
    for iter = 1:iterM
        decoded = zeros(N, d);
        for i = 1:d
            segment = pop(:, (i-1)*bit_length+1:i*bit_length);
            vals = segment * (2.^(bit_length-1:-1:0))';
            decoded(:, i) = lb(i) + vals / (2^bit_length - 1) * (ub(i) - lb(i));
        end
    
        fitness = zeros(N, 1);
        for i = 1:N
            fitness(i) = f(decoded(i,:));
        end
    
        [best_val, idx] = min(fitness);
        if best_val < gBV
            gBV = best_val;
            gBpos = decoded(idx,:);
        end
        % gBV_record(iter) = gBV;
        gBV_record=[gBV_record;gBV];  % 保存每一代的全局最优值

    
        % 轮盘赌选择
        ticket = 1./(fitness + eps);
        cdf = cumsum(ticket)/sum(ticket);
        newpop = zeros(size(pop));
        for i = 1:N
            r = rand;
            selIdx = find(cdf >= r, 1, 'first');
            newpop(i,:) = pop(selIdx,:);
        end
    
        % 单点交叉
        for i = 1:2:N-1
            if rand < p_cr
                point = randi([1, total_bits-1]);
                newpop([i, i+1], :) = [...
                    [newpop(i,1:point), newpop(i+1,point+1:end)];
                    [newpop(i+1,1:point), newpop(i,point+1:end)] ];
            end
        end
    
        % 变异
        mask = rand(size(newpop)) < p_mut;
        newpop(mask) = 1 - newpop(mask);
        newpop(1,:) = pop(idx,:);  % 保留最优个体
        pop = newpop;
    
        % % 动态绘图
        % if mod(iter, 5) == 0 || iter == 1 || iter == iterM
        %     fprintf('GA Iter %d: Best Fitness = %.6f\n', iter, gBV);
        %     figure(1); clf;
        %     plot(gBV_record(1:iter), 'b-o');
        %     xlabel('Iteration'); ylabel('Fitness');
        %     title('GA Convergence Progress');
        %     grid on; drawnow;
        % end


                % % 每5次迭代或最后一次迭代保存数据
        % if mod(iter, 5) == 0 || iter == iterM
        %     data_file1 = fullfile(output_dir, 'ga_temp_data1.mat');
        %     save(data_file1, 'gBV_record', 'iter', 'iterM');
        % end

        % 每次迭代完成后发布收敛数据
        servo_save_progress(data_file, gBV_record, iter);

    end
    
    % fprintf('\n[GA] Optimal value: %.6f\n', gBV);
    % disp('[GA] Best parameters:');
    % disp(gBpos);
    % 
    % save('gBV_record_data_gaITSE.mat', 'gBV_record');
    
    % 仿真阶段
    g = gBpos;

    [~, time, reference0, position] = fun_position(gBpos, T, objective);
end
