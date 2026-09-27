function matlab_regressions(project_root)
% Pure numerical checks; no model simulation or optimization benchmark.
addpath(fullfile(project_root, 'matlab_scripts', 'optimization', 'single_objective'));
addpath(fullfile(project_root, 'matlab_scripts', 'optimization', 'common'));
addpath(fullfile(project_root, 'matlab_scripts', 'common'));
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
% HV uses physical units and a fixed reference box across populations/runs.
[empty_hv, cfg] = servo_hypervolume(zeros(0,3));
assert(empty_hv == 0 && isequal(cfg.scale, [0.025,20,0.5]));
ref = cfg.reference;
point = 0.5 * ref;
assert(abs(servo_hypervolume(point) - 0.125) < 1e-12);
% Feasible 11% overshoot was outside the old synthetic reference box.
assert(myHV(point, GetOptimum(3,6)) == 0);
assert(abs(servo_hypervolume([point; point; 0.75*ref]) - 0.125) < 1e-12);
assert(servo_hypervolume(ref) == 0);
[h, cfg] = servo_hypervolume([point; inf,inf,inf; nan,1,1; 2*ref]);
assert(abs(h-0.125)<1e-12 && cfg.invalid_count==2 && cfg.outside_reference_count==1);
assert(servo_hypervolume([inf,inf,inf]) == 0);
% Independent inclusion-exclusion formula for a two-box union.
points = [0.2,0.6,0.3; 0.5,0.2,0.4] .* ref;
q = points ./ ref;
expected_hv = sum(prod(1-q,2)) - prod(1-max(q,[],1));
assert(abs(servo_hypervolume(points)-expected_hv) < 1e-12);
assert(servo_hypervolume([points; 0.1*ref]) >= servo_hypervolume(points));
rejected = false;
try, servo_hypervolume([-0.01,1,0.1]);
catch e, rejected = strcmp(e.identifier,'Servo:InvalidHVObjectives'); end
assert(rejected);
% Progress publication preserves the old fields and the new archive evidence.
file = [tempname '.mat'];
clean_file = onCleanup(@() delete(file));
servo_save_progress(file, [h,0], 1);
record = load(file); assert(record.iter==1 && ~isfield(record,'diagnostics'));
details = struct('archive_objectives', {{point}}, 'hv', cfg);
servo_save_progress(file, [h,0], 1, details);
record = load(file);
assert(isequal(record.diagnostics.archive_objectives{1},point));
assert(record.gBV_record(1)==h && record.iter==1);
fprintf('PASS: four objectives, archive/selection, physical HV and progress evidence.\n');
end
