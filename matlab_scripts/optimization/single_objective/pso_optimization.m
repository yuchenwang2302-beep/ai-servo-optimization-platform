function [gBV, gBpos, time, reference0, position] = pso_optimization(N1, d, interM, objective)
    if nargin < 4, objective = 'ITSE'; end
    clc;   % clear;
    
    % % 粒子群参数
    % N1 = 50;           % 粒子数量
    % d = 11;             % 参数维度
    % interM = 50;        % 最大迭代次数

    % 强制所有输入转为 double
    N1 = double(N1);
    d = double(d);
    interM = double(interM);
    
    c1 = 1.5; c2 = 1.5;
    omega_max = 0.9; omega_min = 0.4;
    
    [lb, ub] = servo_search_bounds('standard');
    
    % 初始种群和速度
    pop = repmat(lb, N1, 1) + rand(N1, d) .* (repmat(ub - lb, N1, 1));
    v = -0.1 * repmat(ub - lb, N1, 1) + 0.2 * rand(N1, d) .* repmat(ub - lb, N1, 1);
    
    pBV = ones(N1,1)*inf;
    gBV = inf;
    pBpos = pop;
    gBpos = zeros(1,d);
    
    % gBV_record = zeros(interM, 1);
    gBV_record = [];
    
    % % 打开并行池（如尚未打开）
    % if isempty(gcp('nocreate'))
    %     parpool('local');
    % end
    
    % % 图像初始化
    % figure;
    % hold on;
    % h = plot(NaN, NaN, 'b-o', 'LineWidth', 1.5);
    % xlabel('Iteration'); ylabel('Best Fitness Value');
    % title('PSO Iteration Progress (Parallel)');
    % grid on;
    % refresh_interval = 5;
    
    % 目标函数
    T = 0.5;
    f = @(x) fun_position(x, T, objective);

    % 在循环之前添加数据文件初始化
    data_file = 'pso_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end
    
    % 主迭代循环
    for iter = 1:interM
        f_value = zeros(N1, 1);
    
        % 并行适应度计算
        for i = 1:N1
            % Evaluate each candidate once.
            % f_value(i) = 0.3*abs(val(1)) + 0.4*abs(val(2)) + 0.3*abs(val(3));  % 可根据需要加权
           f_value(i) = f(pop(i,:));
    
        end
    
        % 更新个体极值和全局极值
        for i = 1:N1
            if f_value(i) < pBV(i)
                pBV(i) = f_value(i);
                pBpos(i,:) = pop(i,:);
            end
            if pBV(i) < gBV
                gBV = pBV(i);
                gBpos = pBpos(i,:);
            end
        end
    
        % 更新速度和位置
        for i = 1:N1
            r1 = rand(1,d); r2 = rand(1,d);
            omega = omega_max - (omega_max - omega_min) * iter / interM;
            v(i,:) = omega * v(i,:) + c1*r1.*(pBpos(i,:) - pop(i,:)) + c2*r2.*(gBpos - pop(i,:));
            v(i,:) = max(min(v(i,:), ub - lb), -abs(ub - lb));
            pop(i,:) = pop(i,:) + v(i,:);
            pop(i,:) = max(min(pop(i,:), ub), lb);
        end
    
        % gBV_record(iter) = gBV;
        gBV_record=[gBV_record;gBV];  % 保存每一代的全局最优值
    
        % if mod(iter, refresh_interval) == 0 || iter == 1 || iter == interM
        %     set(h, 'XData', 1:iter, 'YData', gBV_record(1:iter));
        %     drawnow;
        %     pause(0.01);
        % end

        % 每次迭代完成后发布收敛数据
        servo_save_progress(data_file, gBV_record, iter);
    end
    
    % fprintf('optimal_value is %.6f\\n', gBV);
    % disp('the corresponding position is:');
    % disp(gBpos);
    g = gBpos;
    % figure;
    % plot(1:interM, gBV_record, 'b-o', 'LineWidth', 1.5);
    % xlabel('Iteration');
    % ylabel('Best Fitness Value');
    % title('PSO Iteration Progress');
    % grid on;
    % 
    % save('gBV_record_data_parallelITSE.mat', 'gBV_record');
    % run Data.m

    [~, time, reference0, position] = fun_position(gBpos, T, objective);
end
