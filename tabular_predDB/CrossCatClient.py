#
# Copyright 2013 Baxter, Lovell, Mangsingkha, Saeedi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import os
import inspect
#
import tabular_predDB.EngineTemplate as EngineTemplate


class CrossCatClient(object):

    def __init__(self, engine):
        self.engine = engine
        return

    def __getattribute__(self, name):
        engine = object.__getattribute__(self, 'engine')
        attr = None
        if hasattr(engine, name):
            attr = getattr(engine, name)
        else:
            attr = object.__getattribute__(self, name)
        return attr


if __name__ == '__main__':
    import tabular_predDB.python_utils.data_utils as du
    import tabular_predDB.LocalEngine as LocalEngine
    le = LocalEngine.LocalEngine(0)
    ccc = CrossCatClient(le)

    gen_seed = 0
    num_clusters = 4
    num_cols = 8
    num_rows = 16
    num_splits = 1
    max_mean = 10
    max_std = 0.1
    T, M_r, M_c = du.gen_factorial_data_objects(
        gen_seed, num_clusters,
        num_cols, num_rows, num_splits,
        max_mean=max_mean, max_std=max_std,
        )
    M_c_prime, M_r_prime, X_L, X_D, = ccc.initialize(M_c, M_r, T)
