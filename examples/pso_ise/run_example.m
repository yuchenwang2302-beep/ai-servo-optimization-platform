function output_dir = run_example()
%RUN_EXAMPLE Run a small, seeded PSO/ISE example in a separate output folder.
% From the repository root in MATLAB R2024b:
%   addpath(fullfile(pwd, 'examples', 'pso_ise')); run_example
% Requires Simulink and Motor Control Blockset, as does the desktop UI.

    root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
    original_path = path;
    original_folder = pwd;
    original_rng = rng;
    model = 'Jerk_FF_Step_2023';
    already_loaded = bdIsLoaded(model);
    restore = onCleanup(@() restore_session(original_path, original_folder, original_rng, model, already_loaded)); %#ok<NASGU>

    addpath(fullfile(root, 'matlab_scripts', 'common'));
    addpath(fullfile(root, 'matlab_scripts', 'optimization', 'common'));
    addpath(fullfile(root, 'matlab_scripts', 'optimization', 'single_objective'));
    output_root = fullfile(root, 'runtime', 'examples', 'pso_ise');
    if ~isfolder(output_root), mkdir(output_root); end
    output_dir = tempname(output_root);
    mkdir(output_dir);
    cd(output_dir);

    rng(42, 'twister');
    started = tic;
    [best, parameters, time, reference, position] = pso_optimization(2, 11, 3, 'ISE');
    compute_seconds = toc(started);
    time = double(time(:)); reference = double(reference(:)); position = double(position(:));
    independent_ise = trapz(time(:), (position(:) - reference(:)).^2);
    progress = load('pso_temp_data.mat', 'gBV_record', 'iter');
    curve = progress.gBV_record(:);
    assert(progress.iter == 3 && numel(curve) == 3 && all(isfinite(curve)), 'Incomplete convergence data.');
    assert(all(diff(curve) <= 1e-12), 'Best-so-far fitness must be non-increasing.');
    assert(isfinite(best) && abs(best - independent_ise) <= max(1e-10, abs(best)*1e-6), 'ISE verification failed.');
    assert(abs(best - curve(end)) <= max(1e-10, abs(best)*1e-6), 'Final curve value differs from result.');

    summary = struct('algorithm', 'PSO', 'objective', 'ISE', 'population', 2, ...
        'dimensions', 11, 'iterations', 3, 'seed', 42, 'generator', 'twister', ...
        'matlab_release', version('-release'), 'objective_value', best, ...
        'independent_ise', independent_ise, 'compute_seconds', compute_seconds, ...
        'convergence', curve', 'best_parameters', parameters(:)', ...
        'tracking_sample_stride', 10);
    file = fopen('summary.json', 'w');
    assert(file ~= -1, 'Cannot write example summary.');
    close_file = onCleanup(@() fclose(file));
    fprintf(file, '%s\n', jsonencode(summary, 'PrettyPrint', true));
    clear close_file;

    % Keep every tenth point for a small public plotting example; ISE uses all points.
    indices = unique([1:10:numel(time), numel(time)]);
    samples = table(time(indices(:)), reference(indices(:)), position(indices(:)), ...
        'VariableNames', {'time_s', 'reference_position', 'actual_position'});
    writetable(samples, 'tracking.csv');
    save('full_result.mat', 'time', 'reference', 'position', 'best', 'parameters', 'curve');
    fprintf('PASS: 3 iterations; returned ISE agrees with independent integration.\n');
    fprintf('Results: %s\n', output_dir);
end

function restore_session(original_path, original_folder, original_rng, model, already_loaded)
    if ~already_loaded && bdIsLoaded(model), close_system(model, 0); end
    cd(original_folder);
    path(original_path);
    rng(original_rng);
end
