%% Generate points on the Pareto front
function R = GetOptimum(M, N)
% 生成 Pareto 前沿的参考点，用于性能评估
R = UniformPoint(N, M);
R = R ./ repmat(sqrt(sum(R.^2, 2)), 1, M);
end