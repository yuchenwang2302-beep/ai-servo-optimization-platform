function matlab_regressions(project_root)
% Pure numerical checks; no model simulation or optimization benchmark.
addpath(fullfile(project_root, 'matlab_scripts', 'optimization', 'single_objective'));
addpath(fullfile(project_root, 'matlab_scripts', 'optimization', 'common'));
addpath(genpath(fullfile(project_root, 'matlab_scripts', 'optimization', 'multi_objectives')));
t = [0;1;2]; r = zeros(3,1); y = [1;2;3];
names = {'ITSE','ISE','IAE','ITAE'};
expected = [13,9,4,5];
[lb,ub] = servo_search_bounds('standard');
assert(isequal(lb,[1,2783.7,.867,17.2799,.1,1e-4,1e-9,10,10,10,50]));
assert(isequal(ub,[5,10398,5,100,3,.1,1e-3,30,50,80,500]));
[mlb,mub] = servo_search_bounds('mdf');
assert(isequal(mlb,[lb(1:10),10]) && isequal(mub,[ub(1:7),300,300,300,300]));
for k = 1:4
    assert(abs(servo_error_metric(t,r,y,names{k})-expected(k)) < 1e-12);
end
[X,F,n] = UpdateArchive(zeros(100,2),inf(100,3),[1,2,3;1,2,3],[1,1,1;1,1,1;2,2,2],0);
assert(n == 1 && isequal(F,[1,1,1]) && size(X,1) == 1);
ranks = RankingProcess(F,8,3);
assert(isequal(ranks,1));
assert(RouletteWheelSelection(1./ranks) == 1);
[X,F,n] = UpdateArchive(X,F,[4;4],[inf,inf,inf],n);
assert(n == 1 && all(isfinite(F(:))));
[X,F,n] = UpdateArchive(zeros(0,2),zeros(0,3),[1;1],[inf,inf,inf],0);
assert(n == 0 && isempty(X) && isempty(F));
F = [1,2,3;2,1,3;3,1,2]; X = [1,1;2,2;3,3];
[X,F,ranks,n] = HandleFullArchive(X,F,3,RankingProcess(F,2,3),2);
assert(n == 2 && size(X,1) == 2 && size(F,1) == 2 && numel(ranks) == 2);
for k = 1:50
    index = RouletteWheelSelection([0,0]);
    assert(ismember(index,[1,2]));
end
fprintf('PASS: four objectives and archive/selection edge cases.\n');
end
