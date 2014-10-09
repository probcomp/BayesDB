#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Jay Baxter and Dan Lovell
#   Authors: Jay Baxter, Dan Lovell, Baxter Eaves, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import numpy as np

# there should be a 'get' method for each item in diagnosics lists
multi_state_diagnostics = []
single_state_diagnostics = [
    'num_views',
    'column_crp_alpha',
    'min_clusters_view',
    'max_clusters_view',
    'mean_clusters_view',
    'std_clusters_view'
]

# muti-state diagnostics

# single-state methods
def get_num_views(X_L, X_D):
    """Returns the number of views in X_L
    """
    return len(X_L['column_partition']['counts'])


def get_column_crp_alpha(X_L, X_D):
    """Retruns column crp alpha parameter
    """
    return X_L['column_partition']['hypers']['alpha']


def get_min_clusters_view(X_L, X_D):
    """ Returns the minimum number of clusters in a view
    """
    Z = np.array(X_D, dtype=int)
    num_clusters_view = np.max(Z, axis=1)+1
    return np.min(num_clusters_view)


def get_max_clusters_view(X_L, X_D):
    """ Returns the maximum number of clusters in a view
    """
    Z = np.array(X_D, dtype=int)
    num_clusters_view = np.max(Z, axis=1)+1
    return np.max(num_clusters_view)


def get_mean_clusters_view(X_L, X_D):
    """ Returns the mean number of clusters in views
    """
    Z = np.array(X_D, dtype=int)
    num_clusters_view = np.max(Z, axis=1)+1
    return np.mean(num_clusters_view)


def get_std_clusters_view(X_L, X_D):
    """ Returns the standard deviation of numbers of clusters in views
    """
    Z = np.array(X_D, dtype=int)
    num_clusters_view = np.max(Z, axis=1)+1
    return np.std(num_clusters_view)
