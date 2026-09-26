function [gBV, gBpos, time, reference0, position] = ia_optimization(NP, d, iterM, objective)
    if nargin < 4, objective = 'ITSE'; end
    clc; % clear;
    % vref = 200;
    T = 0.5;
    % d = 11;          % 参数维度（包含扰动/前馈项）
    % NP = 50;        % 个体数量
    % iterM = 50;         % 最大代数

    % 强制所有输入转为 double
    NP = double(NP);
    d = double(d);
    iterM = double(iterM);

    pm = 0.7;        % 变异概率
    alfa = 1;        % 激励度系数
    belta = 1;
    detas = 0.1;     % 相似度阈值
    Ncl = 10;        % 克隆个体数
    deta0 = 0.5;     % 初始变异强度
    
    [lb, ub] = servo_search_bounds('standard');
    
    f = @(x) fun_position(x, T, objective);
    
    % 初始化种群
    pop = repmat(lb', 1, NP) + rand(d, NP) .* repmat((ub - lb)', 1, NP);
    aff = zeros(1, NP);
    for i = 1:NP
        aff(i) = -f(pop(:,i)');
    end
    
    [best_aff, best_idx] = max(aff);
    gBpos = pop(:,best_idx);
    % gBV_record = zeros(iterM, 1);
    gBV_record = [];

    % 在循环之前添加数据文件初始化
    data_file = 'ia_temp_data.mat';
    if exist(data_file, 'file')
        delete(data_file);
    end


    for iter = 1:iterM
        % 浓度因子
        ND = zeros(1, NP);
        for i = 1:NP
            dist = vecnorm(pop - pop(:,i));
            ND(i) = sum(dist < detas) / NP;
        end
    
        score = alfa * aff - belta * ND;
        [~, idx] = sort(score, 'descend');
        elite = pop(:, idx(1:NP/2));
    
        % 克隆变异
        offspring = [];
        aff_new = zeros(1, NP/2);
        for i = 1:NP/2
            a = elite(:,i);
            clones = repmat(a, 1, Ncl);
            deta = deta0 / (iter + 1);
            for j = 2:Ncl
                for d = 1:d
                    if rand < pm
                        clones(d,j) = clones(d,j) + (rand-0.5) * deta;
                    end
                    % 边界控制
                    clones(d,j) = min(max(clones(d,j), lb(d)), ub(d));
                end
            end
            caff = zeros(1, Ncl);
            for j = 1:Ncl
                caff(j) = -f(clones(:,j)');
            end
            [~, bestIdx] = max(caff);
            offspring = [offspring clones(:,bestIdx)];
            aff_new(i) = caff(bestIdx);
        end
    
        % 新个体补充
        newpop = repmat(lb', 1, NP/2) + rand(d, NP/2) .* repmat((ub - lb)', 1, NP/2);
        aff_rnd = zeros(1, NP/2);
        for i = 1:NP/2
            aff_rnd(i) = -f(newpop(:,i)');
        end
    
        % 合并与选择
        pop_all = [offspring, newpop];
        aff_all = [aff_new, aff_rnd];
        ND_all = zeros(1, NP);
        for i = 1:NP
            dist2 = vecnorm(pop_all - pop_all(:,i));
            ND_all(i) = sum(dist2 < detas) / NP;
        end
        score_all = alfa * aff_all - belta * ND_all;
        [~, idx] = sort(score_all, 'descend');
        pop = pop_all(:, idx(1:NP));
        aff = aff_all(idx(1:NP));
    
        [candidate_aff, best_idx] = max(aff);
        if candidate_aff > best_aff
            best_aff = candidate_aff;
            gBpos = pop(:,best_idx);
        end
        gBV_record =[gBV_record;-best_aff];
        gBV = gBV_record(end);
    
        % if mod(iter, 5) == 0 || iter == 1 || iter == iterM
        %     fprintf("Gen %d, Best = %.6f\n", iter, gBV_record(iter));
        %     figure(1); clf;
        %     plot(gBV_record(1:iter), 'b-o');
        %     xlabel('Iteration'); ylabel('Best Fitness');
        %     title(['IA Progress - Gen ' num2str(iter)]);
        %     drawnow;
        % end

        % 每次迭代完成后发布收敛数据
        servo_save_progress(data_file, gBV_record, iter);
    end
    
    % fprintf('\nFinal Best Value: %.6f\n', gBV_record(end));
    % disp('Best Parameter Vector:');
    % disp(gBpos');
    % 
    % save('gBV_record_data_iaITSE.mat', 'gBV_record');
    
    % 仿真与结果保存
    g = gBpos';

    [~, time, reference0, position] = fun_position(gBpos, T, objective);
end
