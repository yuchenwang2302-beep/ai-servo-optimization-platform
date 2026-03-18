%_________________________________________________________________________________
%  Improved Grasshopper Optimization Algorithm with Levy Flight (LFGOA)
%  Based on MOGOA code with Levy Flight integration
%
%  Developed in MATLAB R2016a
%
%  Modified according to the paper:
%  Enhancing grasshopper optimization algorithm (GOA) with levy flight for engineering applications
%____________________________________________________________________________________
function [time, reference0, position] = LVMOGOA(N, ArchiveMaxSize, iterM, dim, obj_no)

clc;
% clear;
close all;

% 强制所有输入转为 double
N = double(N);
ArchiveMaxSize = double(ArchiveMaxSize);
iterM = double(iterM);
dim = double(dim);
obj_no = double(obj_no);

% hv=ones(10,1);
% dm=ones(10,1);
% deltap=ones(10,1);
% nd_solutions=ones(10,1);
% time=ones(10,1);
% for pp=1:10

ObjectiveFunction=@fun_position_2;
% dim=11;
lb = [1, 2.7837e+3,  0.867,  17.2799, 0.1,     1e-4,   1e-9,  10, 10,  10,  50];
ub = [5,      1.0398e+4, 5, 100,   3,       0.1,   1e-3, 30, 50, 80, 500];
% obj_no=3;

if size(ub,2)==1
    ub=ones(1,dim)*ub;
    lb=ones(1,dim)*lb;
end

% 奇偶维度处理
flag=0;
if (rem(dim,2)~=0)
    dim = dim+1;
    ub = [ub, 1];
    lb = [lb, 0];
    flag=1;
end

% iterM=20;
% N=50;
% ArchiveMaxSize=150;

Archive_X=zeros(100,dim);
Archive_F=ones(100,obj_no)*inf;
Archive_member_no=0;

% 初始化种群
GrassHopperPositions = initializationWithLevy(N, dim, ub, lb); % 修改的初始化函数

TargetPosition=zeros(dim,1);
TargetFitness=inf*ones(1,obj_no);

cMax=1;
cMin=0.00004;

cc=ones(iterM,1);
optimum = GetOptimum(obj_no, N);
IGD_values = zeros(1, iterM);  %IGD
HV_values = zeros(1, iterM);   %HV
DM_values = zeros(1, iterM);   %DM
Deltap_values = zeros(1, iterM);
learning_rate_1=zeros(1, iterM);
elapsed_time=zeros(1, iterM);
tic

% 在循环之前添加数据文件初始化
data_file = 'LVMOGOA_temp_data.mat';
if exist(data_file, 'file')
    delete(data_file);
end

% 主循环
for iter=1:iterM
    parfor i = 1:N
        % 确保草蜢的位置在边界内
        Flag4ub = GrassHopperPositions(:, i) > ub';
        Flag4lb = GrassHopperPositions(:, i) < lb';
        GrassHopperPositions(:, i) = (GrassHopperPositions(:, i) .* (~(Flag4ub + Flag4lb))) + ub' .* Flag4ub + lb' .* Flag4lb;

        % 并行计算目标函数值

        GrassHopperFitness(i, :) = ObjectiveFunction(GrassHopperPositions(:, i)',0);
    end

    % 在并行外部更新 TargetFitness 和 TargetPosition
    for i = 1:N
        if dominates(GrassHopperFitness(i, :), TargetFitness)
            TargetFitness = GrassHopperFitness(i, :);  % 更新目标适应度
            TargetPosition = GrassHopperPositions(:, i);  % 更新目标位置
        end
    end

    % 更新存档
    [Archive_X, Archive_F, Archive_member_no]=UpdateArchive(Archive_X, Archive_F, GrassHopperPositions, GrassHopperFitness, Archive_member_no);

    if Archive_member_no>ArchiveMaxSize
        Archive_mem_ranks=RankingProcess(Archive_F, ArchiveMaxSize, obj_no);
        [Archive_X, Archive_F, Archive_mem_ranks, Archive_member_no]=HandleFullArchive(Archive_X, Archive_F, Archive_member_no, Archive_mem_ranks, ArchiveMaxSize);
    else
        Archive_mem_ranks=RankingProcess(Archive_F, ArchiveMaxSize, obj_no);
    end

    % 选择目标
    index=RouletteWheelSelection(1./Archive_mem_ranks);
    if index==-1
        index=1;
    end
    TargetFitness=Archive_F(index,:);
    TargetPosition=Archive_X(index,:)';

    % 更新参数c
    c=cMax-iter*((cMax-cMin)/iterM);
    cc(iter)=c;

    % 位置更新
    for i=1:N
        temp= GrassHopperPositions;
        S_i_total = zeros(dim,1);

        % 社会力计算
        for k=1:2:dim
            S_i=zeros(2,1);
            for j=1:N
                if i~=j
                    Dist=distance(temp(k:k+1,j), temp(k:k+1,i));
                    r_ij_vec=(temp(k:k+1,j)-temp(k:k+1,i))/(Dist+eps);
                    xj_xi=2+rem(Dist,2);

                    % 社会力公式
                    s_ij=((ub(k:k+1)' - lb(k:k+1)') .*c/2)*S_func(xj_xi).*r_ij_vec;
                    S_i=S_i+s_ij;
                end
            end
            S_i_total(k:k+1) = S_i;
        end

        % 基础位置更新
        X_new = c*S_i_total + TargetPosition;

        % 加入Levy Flight扰动
        levy_step = LevyFlight(dim)';
        X_new = X_new + 0.01*levy_step; % f=0.01

        % 边界处理
        X_new = max(X_new, lb');
        X_new = min(X_new, ub');

        GrassHopperPositions_temp(i,:) = X_new';
    end

    GrassHopperPositions = GrassHopperPositions_temp';

    % 计算性能指标
    toc
    elapsed_time(iter) = toc;
    IGD_values(iter) = myIGD(Archive_F, optimum);  % 使用 PlatEMO 的 IGD 计算方法
    HV_values(iter) = myHV(Archive_F, optimum);    % 使用 PlatEMO 的 HV 计算方法
    DM_values(iter) = myDM(Archive_F, optimum);    % 使用 PlatEMO 的 HV 计算方法
    Deltap_values(iter) = myDeltaP(Archive_F,optimum);
    % disp(['Iter ', num2str(iter), ': IGD=', num2str(IGD_values(iter)), ' HV=', num2str(HV_values(iter))]);

    % 每5次迭代或最后一次迭代时保存数据
    gBV_record = HV_values;
    if mod(iter, 5) == 0 || iter == iterM
        save(data_file, 'gBV_record', 'iter');
    end

end

% 后处理
if (flag==1)
    TargetPosition = TargetPosition(1:dim-1);
end

%%选择TOPSIS
f_matrix=Archive_F;
original_indices = (1:size(f_matrix, 1))';
% 找到包含 inf 的行
inf_rows = any(isinf(f_matrix), 2);
% 去除包含 inf 的行，并保留有效行的索引
filtered_f_matrix = f_matrix(~inf_rows, :);
filtered_indices = original_indices(~inf_rows);
% 标准化决策矩阵 (基于最小值)
min_values = min(filtered_f_matrix);
max_values = max(filtered_f_matrix);
f_matrix_norm = (max_values - filtered_f_matrix) ./ (max_values - min_values);
% 定义权重向量 (根据实际优先级调整)
% weights = [10, 10, 0.1, 1, 0.2, 0.2];
weights = [0.5,0.4,0.1];
%稳态误差 超调 上升时间 调整时间 振荡次数 RMSE
% 构建加权标准化矩阵
weighted_matrix = f_matrix_norm .* weights;
% 确定理想解 (最优情况) 和反理想解 (最差情况)
ideal_solution = max(weighted_matrix); % 理想解是所有列的最小值
negative_ideal_solution = min(weighted_matrix); % 反理想解是所有列的最大值
% 计算到理想解和反理想解的欧几里得距离
distance_to_ideal = sqrt(sum((weighted_matrix - ideal_solution).^2, 2));
distance_to_negative_ideal = sqrt(sum((weighted_matrix - negative_ideal_solution).^2, 2));
% 计算相对接近度
relative_closeness = distance_to_negative_ideal ./ (distance_to_ideal + distance_to_negative_ideal);
% 找到相对接近度最大的解
[~, best_solution_index] = max(relative_closeness);
% 找到最佳解在原始矩阵中的索引
best_solution_original_index = filtered_indices(best_solution_index);
% 输出最佳解的原始索引和相对接近度
% disp(['最佳解在原始矩阵中的索引为: ', num2str(best_solution_original_index)]);
% disp(['最佳解的相对接近度为: ', num2str(relative_closeness(best_solution_index))]);
% 如果需要，可以进一步查看这个解的具体指标
best_solution = f_matrix(best_solution_original_index, :);
% disp(['最佳解的指标值为: ', num2str(best_solution)]);
g=Archive_X(best_solution_original_index,:);




results=T_Jerk_FF_Step_2023_2(g,0);

% 从 results 中提取三个变量
time = results(:,1);         % 时间序列
reference0 = results(:,2);   % 参考信号
position = results(:,3);     % 位置响应

% % 调试输出 - 检查数据点数
% disp(['MATLAB端数据点数: ', num2str(length(results))]);


%     time(pp)=elapsed_time(end);
%     hv(pp)=HV_values(end);
%     dm(pp)=DM_values(end);
%     nd_solutions(pp)=Archive_member_no;
%     deltap(pp)=Deltap_values(end);
% end
% hv_mean=mean(hv);
% dm_mean=mean(dm);
% nd_solutions_mean=mean(nd_solutions);
% Deltap_values_mean=mean(deltap);
% time_mean=mean(time);
%
% aa=[hv dm deltap time nd_solutions];
% aaa=[hv_mean dm_mean Deltap_values_mean time_mean nd_solutions_mean];
% % 可视化
% figure
% Draw_DTLZ5_3();
% hold on
% plot3(Archive_F(:,1),Archive_F(:,2),Archive_F(:,3),'ro','MarkerSize',8,'markerfacecolor','k');
% legend('True PF','Obtained PF');
% title('LFGOA');
%
% figure;
% subplot(1,2,1);
% plot(1:max_iter, IGD_values, '-o');
% title('IGD over iterations');
% xlabel('Iteration');
% ylabel('IGD');
%
% subplot(1,2,2);
% plot(1:max_iter, HV_values, '-o');
% title('HV over iterations');
% xlabel('Iteration');
% ylabel('HV');



