function objective_value = verify_reference()
%VERIFY_REFERENCE Re-evaluate recorded parameters without an optimizer search.
% Requires the same model and toolboxes as run_example.
    root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
    original_path = path;
    original_folder = pwd;
    original_rng = rng;
    model = 'Jerk_FF_Step_2023';
    already_loaded = bdIsLoaded(model);
    restore = onCleanup(@() restore_session(original_path, original_folder, original_rng, model, already_loaded)); %#ok<NASGU>

    addpath(fullfile(root, 'matlab_scripts', 'optimization', 'common'));
    addpath(fullfile(root, 'matlab_scripts', 'optimization', 'single_objective'));
    record = jsondecode(fileread(fullfile(root, 'examples', 'pso_ise', 'reference', 'summary.json')));
    output_root = fullfile(root, 'runtime', 'examples', 'pso_ise');
    if ~isfolder(output_root), mkdir(output_root); end
    output_dir = tempname(output_root);
    mkdir(output_dir);
    cd(output_dir);

    [objective_value, time, reference, position] = fun_position(record.best_parameters(:)', 0.5, 'ISE');
    independent_ise = trapz(double(time(:)), (double(position(:)) - double(reference(:))).^2);
    tolerance = max(1e-10, abs(record.objective_value)*1e-6);
    assert(isfinite(objective_value) && abs(objective_value - record.objective_value) <= tolerance, ...
        'Recorded parameters did not reproduce the reference ISE in this environment.');
    assert(abs(objective_value - independent_ise) <= tolerance, 'Independent ISE verification failed.');
    fprintf('PASS: recorded parameters reproduce ISE %.12g.\n', objective_value);
    fprintf('Simulation working directory: %s\n', output_dir);
end

function restore_session(original_path, original_folder, original_rng, model, already_loaded)
    if ~already_loaded && bdIsLoaded(model), close_system(model, 0); end
    cd(original_folder);
    path(original_path);
    rng(original_rng);
end
