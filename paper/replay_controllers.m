function outputFolder = replay_controllers(outputFolder)
% Evaluate the saved paper controllers with the supplied Simulink models.
% From the repository root: addpath('paper'); replay_controllers;
arguments
    outputFolder (1,:) char = ''
end
paperRoot = fileparts(mfilename('fullpath'));
projectRoot = fileparts(paperRoot);
if isempty(outputFolder)
    outputFolder = fullfile(projectRoot, 'runtime', 'paper_replay');
end
if ~isfolder(outputFolder), mkdir(outputFolder); end
outputFolder = char(java.io.File(outputFolder).getCanonicalPath());
oldFolder = pwd;
oldPath = path;
oldRng = rng;
oldModels = find_system('Type', 'block_diagram');
restoreFolder = onCleanup(@() cd(oldFolder)); %#ok<NASGU>
restorePath = onCleanup(@() path(oldPath)); %#ok<NASGU>
restoreRng = onCleanup(@() rng(oldRng)); %#ok<NASGU>
restoreModels = onCleanup(@() closeNewModels(oldModels)); %#ok<NASGU>
addpath(fullfile(projectRoot, 'matlab_scripts', 'common'));
addpath(fullfile(projectRoot, 'matlab_scripts', 'optimization', 'common'));
addpath(fullfile(projectRoot, 'matlab_scripts', 'optimization', 'single_objective'));
addpath(genpath(fullfile(projectRoot, 'matlab_scripts', 'optimization', 'multi_objectives')));
cd(outputFolder);
parameters = readtable(fullfile(paperRoot, 'data', 'controller_parameters.csv'));
records = jsondecode(fileread(fullfile(paperRoot, 'data', 'results.json')));
names = {'pso', 'midpoint', 'all_upper', 'low_overshoot', 'fast_settling', 'gui_selected'};
report = struct([]);
for k = 1:numel(names)
    name = names{k};
    x = reshape(parameters.(name), 1, []);
    if k <= 3
        [value, time, reference, position] = fun_position(x, 0.5, 'ISE');
        time = double(time(:)); reference = double(reference(:)); position = double(position(:));
        expected = records.single_objective_checks.(name);
        ise = trapz(time, (position-reference).^2);
        assert(abs(value-expected.ISE) <= 1e-10+1e-7*abs(expected.ISE), 'ISE differs for %s.', name);
        assert(abs(ise-value) <= 1e-10+1e-7*abs(value), 'Independent ISE differs for %s.', name);
        band = 0.02*abs(reference(end));
        outside = find(time >= 0.5 & abs(position-reference) > band, 1, 'last');
        if isempty(outside), settling = 0;
        elseif outside == numel(time), settling = NaN;
        else, settling = time(outside+1)-0.5; end
        steady = NaN;
        overshoot = max(0, (max(position)-reference(end))/abs(reference(end))*100);
        assert(abs(overshoot-expected.overshoot_percent) < 1e-3, 'Overshoot differs for %s.', name);
        assert(abs(settling-expected.settling_2percent_seconds) < 2e-4, 'Settling differs for %s.', name);
    else
        simOut = simulate_servo_position(x, 0, 'Jerk_FF_Step_2023_2');
        originalTime = simOut.Pos_Fb_PU.time;
        originalReference = simOut.Ref_Step_PU0.signals.values;
        originalPosition = simOut.Pos_Fb_PU.signals.values;
        desired = originalReference(end);
        steady = double(abs(desired-mean(originalPosition(originalTime >= originalTime(end)-0.15))));
        overshoot = double(max(0, (max(originalPosition)-desired)/max(abs(desired),eps)*100));
        outside = find(originalPosition > desired+0.005 | originalPosition < desired-0.005, 1, 'last');
        if steady > 0.01, settling = 0.5;
        elseif isempty(outside), settling = 0;
        else, settling = double(max(0, originalTime(outside)-0.5)); end
        if strcmp(name, 'gui_selected')
            expected = records.multiobjective.selected_response_objectives(:);
        else
            expected = records.archive_pair.cases.(name).replay_objectives(:);
        end
        assert(all(abs([steady;overshoot;settling]-expected) <= [1e-6;1e-3;2e-4]), ...
            'Multi-objective metrics differ for %s.', name);
        time = double(originalTime(:)); reference = double(originalReference(:)); position = double(originalPosition(:));
        ise = trapz(time, (position-reference).^2);
        band = 0.005;
    end
    writetable(table(time, reference, position, 'VariableNames', {'time_s','reference_pu','position_pu'}), ...
        fullfile(outputFolder, [name '.csv']));
    report(k) = struct('controller', name, 'ISE', ise, 'overshoot_percent', overshoot, ...
        'settling_measure_s', settling, 'settling_band_pu', band, 'steady_state_error_pu', steady); %#ok<AGROW>
    fprintf('Passed %s\n', name);
end
writetable(struct2table(report), fullfile(outputFolder, 'metrics.csv'));
fprintf('Saved controller replays in %s\n', outputFolder);
end

function closeNewModels(oldModels)
models = {'Jerk_FF_Step_2023', 'Jerk_FF_Step_2023_2'};
for k = 1:numel(models)
    if bdIsLoaded(models{k}) && ~ismember(models{k}, oldModels)
        close_system(models{k}, 0);
    end
end
end
