function workers = servo_parallel_workers(N)
% Bound desktop memory use; run serially when the parallel toolbox is absent.
workers = 0;
if ~license('test', 'Distrib_Computing_Toolbox')
    return;
end
try
    pool = gcp('nocreate');
    if isempty(pool)
        % A Simulink worker loads its own model and toolbox data. On a desktop
        % with little free RAM, serial evaluation is safer than another pool.
        if ~ispc
            return;
        end
        [~, system_memory] = memory;
        if system_memory.PhysicalMemory.Available < 6 * 1024^3
            return;
        end
        pool = parpool('Processes', min(2, N));
    end
    workers = min([2, N, pool.NumWorkers]);
catch exception
    warning('Servo:SerialFallback', 'Parallel pool unavailable; running serially: %s', exception.message);
end
end
