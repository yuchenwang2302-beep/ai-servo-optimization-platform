function [score, settings] = servo_hypervolume(objectives)
% Normalized minimization HV for the supplied 0.5-p.u., 1-s servo step model.
% Columns: steady-state error [p.u.], overshoot [%], settling time [s].
% Fixed scales follow fun_position_2's feasibility limits and post-step horizon.
% myHV adds a 10% margin; no estimated/known Pareto front is required here.
% If the reference command, feasibility limits or horizon changes, update these
% scales before comparing runs. The metric never affects archive selection.
validateattributes(objectives, {'numeric'}, {'real', '2d', 'ncols', 3});
settings.version = 'servo-step-hv-v1';
settings.objective_names = {'steady_state_error', 'overshoot', 'settling_time'};
settings.objective_units = {'p.u.', 'percent', 's'};
settings.lower = [0, 0, 0];
settings.scale = [0.025, 20, 0.5];
settings.reference = 1.1 * settings.scale;
settings.normalization = 'volume divided by prod(reference - lower)';
finite_rows = all(isfinite(objectives), 2);
values = double(objectives(finite_rows, :));
if any(values(:) < 0)
    error('Servo:InvalidHVObjectives', 'Servo objectives must be nonnegative.');
end
settings.invalid_count = sum(~finite_rows);
settings.outside_reference_count = sum(any(values > settings.reference, 2));
settings.finite_count = size(values, 1);
if isempty(values)
    score = 0;
else
    score = myHV(values, settings.scale);
end
end
