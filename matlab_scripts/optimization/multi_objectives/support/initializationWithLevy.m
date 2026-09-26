% 改进的初始化函数
function Positions = initializationWithLevy(N, dim, ub, lb)
    Positions = zeros(dim, N);
    % 第一个个体随机初始化
    Positions(:,1) = lb' + (ub' - lb').*rand(dim,1);
    % 其他个体使用Levy Flight初始化
    for j=2:N
        levy_step = LevyFlight(dim);
        % 将Levy步长缩放到[0,1]范围
        scaled_step = (levy_step - min(levy_step)) / (max(levy_step) - min(levy_step) + eps);
        % 映射到问题空间
        Positions(:,j) = lb' + (ub' - lb') .* scaled_step';
        % 边界处理
        Positions(:,j) = max(Positions(:,j), lb');
        Positions(:,j) = min(Positions(:,j), ub');
    end
end