import pylab
pylab.ion()
pylab.show()
import numpy


# settings
N_runs = 5

# generate a time series of stochastic decay
def decay_to(start, end, decay_rate, std, forcing_func, max_iters=500, seed=0):
    random_state = numpy.random.RandomState(seed)
    values = [start]
    for iter_idx in range(max_iters):
        last_value = values[-1]
        residual = last_value - end
        residual *= numpy.exp(decay_rate)
        residual += random_state.normal(scale=std)
        residual += forcing_func(iter_idx)
        new_value = residual + end
        values.append(new_value)
    return values

def N_decay_to(N, start, end, decay_rate, std, forcing_func, max_iters=500):
    runs = []
    for run_idx in range(N):
        run = decay_to(start, end, decay_rate, std, forcing_func,
                       seed=run_idx)
        runs.append(run)
    runs = numpy.array(runs, dtype=int).T
    runs = numpy.clip(runs, 1, numpy.inf)
    return runs

def get_forcing_func(stop_iter, effect_lambda):
    return lambda iter_idx: 0 \
        if iter_idx > stop_iter else effect_lambda(iter_idx)
#
grow_forcing_func = get_forcing_func(10, lambda x: x / 10.)
no_forcing_func = get_forcing_func(0, lambda x: 0.)
shrink_forcing_func = get_forcing_func(10, lambda x: -x / 10.)


N_views_start = 10
N_views_true = 1
# actually generate the data
runs_0 = N_decay_to(N_runs, N_views_start, N_views_true,
                    -.01, 0.2, grow_forcing_func)
runs_1 = N_decay_to(N_runs, N_views_start, N_views_true,
                    -.01, 0.2, no_forcing_func)
runs_2 = N_decay_to(N_runs, N_views_start, N_views_true,
                    -.01, 0.2, shrink_forcing_func)
#
random_state = numpy.random.RandomState(0)
base_time = numpy.array([range(len(runs_0))]).T
base_times = numpy.hstack([base_time] * len(runs_0[0]))
runs_0_times = base_times + random_state.normal(size=(base_times.shape))
runs_1_times = base_times * 0.8 \
    + random_state.normal(size=(base_times.shape))
runs_2_times = base_times * 1.2 \
    + random_state.normal(size=(base_times.shape))

# plot the data
pylab.figure()
pylab.subplot(211)
pylab.title('FAKE DATA')
pylab.plot(runs_0, color='red')
pylab.plot(runs_1, color='blue')
pylab.plot(runs_2, color='black')
pylab.ylabel('# VIEWS')
pylab.xlabel('# ITERATIONS')
pylab.subplot(212)
pylab.plot(runs_0_times, runs_0, color='red')
pylab.plot(runs_1_times, runs_1, color='blue')
pylab.plot(runs_2_times, runs_2, color='black')
pylab.ylabel('# VIEWS')
pylab.xlabel('TIME (SECONDS)')

##########

N_views_start = 10
N_views_true = 10
# actually generate the data
runs_0 = N_decay_to(N_runs, N_views_start, N_views_true,
                    -.01, 0.2, grow_forcing_func)
runs_1 = N_decay_to(N_runs, N_views_start, N_views_true,
                    -.01, 0.2, no_forcing_func)
runs_2 = N_decay_to(N_runs, N_views_start, N_views_true,
                    -.01, 0.2, shrink_forcing_func)
#
random_state = numpy.random.RandomState(0)
base_time = numpy.array([range(len(runs_0))]).T
base_times = numpy.hstack([base_time] * len(runs_0[0]))
runs_0_times = base_times + random_state.normal(size=(base_times.shape))
runs_1_times = base_times * 0.8 \
    + random_state.normal(size=(base_times.shape))
runs_2_times = base_times * 1.2 \
    + random_state.normal(size=(base_times.shape))

# plot the data
pylab.figure()
pylab.subplot(211)
pylab.title('FAKE DATA')
pylab.plot(runs_0, color='red')
pylab.plot(runs_1, color='blue')
pylab.plot(runs_2, color='black')
pylab.ylabel('# VIEWS')
pylab.xlabel('# ITERATIONS')
pylab.subplot(212)
pylab.plot(runs_0_times, runs_0, color='red')
pylab.plot(runs_1_times, runs_1, color='blue')
pylab.plot(runs_2_times, runs_2, color='black')
pylab.ylabel('# VIEWS')
pylab.xlabel('TIME (SECONDS)')
