import argparse
#
import numpy
import pylab


def uniform_to_x_y(uniform_draw, radius=1):
    radians = 2 * numpy.pi * uniform_draw
    x = numpy.cos(radians)
    y = numpy.sin(radians)
    return x, y

def generate_noise(random_state, loc=0, scale=1):
    x_noise = random_state.normal(loc=loc, scale=scale)
    y_noise = random_state.normal(loc=loc, scale=scale)
    return x_noise, y_noise

def draw_N_actual(N, random_state):
    draw_tuple_list = []
    for draw_idx in range(N):
        uniform_draw = random_state.uniform()
        draw_tuple = uniform_to_x_y(uniform_draw)
        draw_tuple_list.append(draw_tuple)
    draw_tuple_arr = numpy.array(draw_tuple_list)
    return draw_tuple_arr

def draw_N_noise(N, random_state, loc=0, scale=0.1):
    draw_tuple_list = []
    for draw_idx in range(N):
        draw_tuple = generate_noise(random_state, loc, scale)
        draw_tuple_list.append(draw_tuple)
    draw_tuple_arr = numpy.array(draw_tuple_list)
    return draw_tuple_arr

def create_ring_data(N, seed, loc=0, scale=0.1):
    random_state = numpy.random.RandomState(seed)
    actual_data = draw_N_actual(N, random_state)
    noise_data = draw_N_noise(N, random_state, loc=loc, scale=scale)
    ring_data = actual_data + noise_data
    return ring_data

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('N', type=int)
    parser.add_argument('--seed', default=0, type=int)
    parser.add_argument('--noise_scale', default=0.1, type=float)
    # args = parser.parse_args()
    args = parser.parse_args(['1000', '--noise_scale', '0.1'])
    N = args.N
    seed = args.seed
    noise_scale = args.noise_scale
    #
    ring_data = create_ring_data(N, seed, 0, noise_scale)
    pylab.figure()
    pylab.scatter(ring_data[:,0], ring_data[:,1])
    pylab.ion()
    pylab.show()
