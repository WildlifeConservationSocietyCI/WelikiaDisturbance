import numpy
import pandas as pd
import settings as s
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import poisson

plt.style.use('ggplot')


#------------------------------------------------------------
# Define the distribution parameters to be plotted
expected_fire_per_km_year = [.0005, .005, .02, .05]
mu_values = [i * 88.423775 for i in expected_fire_per_km_year]

#------------------------------------------------------------
# plot the distributions
#   we generate it using scipy.stats.poisson().  Once the distribution
#   object is created, we have many options: for example
#   - dist.pmf(x) evaluates the probability mass function in the case of
#     discrete distributions.
#   - dist.pdf(x) evaluates the probability density function for
#   evaluates

fig, ax = plt.subplots(figsize=(5, 5))

for mu, i, e in zip(mu_values, [1, 3, 5, 7], expected_fire_per_km_year):
    # create a poisson distribution
    # we could generate a random sample from this distribution using, e.g.
    #   rand = dist.rvs(1000)
    dist = poisson(mu)
    x = np.arange(-1, 200)

    s_plot = int("52%i" % i)

    ax = plt.subplot(s_plot)
    ax.plot(x, dist.pmf(x),
            label='expected human fires=%s $fire/(km^2/yr)$, $(\lambda=%1.3f)$'
                  % (e, mu), linestyle='steps-mid', fillstyle='bottom', color='black')

    plt.xlim(-0.5, 10)
    plt.ylim(0, 1)
    ax.xaxis.set_ticks(np.arange(0, 11, 1))

    legend = ax.legend()
    plt.setp(plt.gca().get_legend().get_texts(), fontsize='8')

    plt.xlabel('$x$')
    plt.ylabel(r'$p(x|\mu)$')

    # cdf plot
    cdf_plot = int("52%i" % (i + 1))
    ax2 = plt.subplot(cdf_plot)
    ax2.plot(x, dist.cdf(x),
            label='expected human fires=%s $fire/(km^2/yr)$, $(\lambda=%1.3f)$' % (e, mu), linestyle='steps-mid',
            fillstyle='bottom', color='black')

    plt.xlim(-0.5, 10)
    plt.ylim(0, 1)
    ax2.xaxis.set_ticks(np.arange(0, 11, 1))

    # plt.title('Poisson Distributions for Expected Frequencies Between 0.0005 - 0.01')

plt.show()
