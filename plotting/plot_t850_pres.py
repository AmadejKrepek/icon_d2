import numpy as np
from multiprocessing import Pool
from functools import partial
import utils
import sys

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')

import matplotlib.pyplot as plt
# The one employed for the figure name when exported 
variable_name = 't850_pres'

utils.print_message('Starting script to plot '+variable_name)

# Get the projection as system argument from the call so that we can 
# span multiple instances of this script outside
if not sys.argv[1:]:
    utils.print_message(
        'Projection not defined, falling back to default (de)')
    projection = 'de'
else:
    projection = sys.argv[1]


def main():
    """In the main function we basically read the files and prepare the variables to be plotted.
    This is not included in utils.py as it can change from case to case."""
    dset = utils.read_dataset(variables=['t', 'pmsl'], level=85000, projection=projection)
    dset['t'] = dset['t'].metpy.convert_units('degC').metpy.dequantify()
    dset['prmsl'] = dset['prmsl'].metpy.convert_units('hPa').metpy.dequantify()

    levels_temp = np.arange(-25., 25., 1.)
    cmap = utils.get_colormap('temp')

    fig = plt.figure(figsize=(utils.figsize_x, utils.figsize_y))

    _ = plt.figure(figsize=(utils.figsize_x, utils.figsize_y))

    ax = plt.gca()
    # Get coordinates from dataset
    m, x, y = utils.get_projection(dset, projection, labels=True)
    dset = dset.drop(['lon', 'lat']).load()

    levels_mslp = np.arange(np.nanmin(dset.prmsl).astype("int"),
                    np.nanmax(dset.prmsl).astype("int"), 7.)

    # All the arguments that need to be passed to the plotting function
    args=dict(x=x, y=y, ax=ax, cmap=cmap,
             levels_temp=levels_temp, levels_mslp=levels_mslp)

    utils.print_message('Pre-processing finished, launching plotting scripts')
    if debug:
        plot_files(dset_level.isel(time=slice(0, 2)), **args)
    else:
        # Parallelize the plotting by dividing into chunks and utils.processes 
        dss = utils.chunks_dataset(dset, utils.chunks_size)
        plot_files_param = partial(plot_files, **args)
        p = Pool(utils.processes)
        p.map(plot_files_param, dss)



def plot_files(dss, **args):
    first = True
    for time_sel in dss.time:
        data = dss.sel(time=time_sel)
        time, run, cum_hour = utils.get_time_run_cum(data)
        # Build the name of the output image
        filename = utils.subfolder_images[projection] + '/' + variable_name + '_%s.png' % cum_hour

        cs = args['ax'].contourf(args['x'], args['y'], data['t'], extend='both', cmap=args['cmap'],
                                    levels=args['levels_temp'])

        c = args['ax'].contour(args['x'], args['y'], data['prmsl'], levels=args['levels_mslp'],
                             colors='white', linewidths=1.)

        labels = args['ax'].clabel(c, c.levels, inline=True, fmt='%4.0f' , fontsize=6)

        maxlabels = utils.plot_maxmin_points(args['ax'], args['x'], args['y'], data['prmsl'],
                                       'max', 80, symbol='H', color='royalblue', random=True)
        minlabels = utils.plot_maxmin_points(args['ax'], args['x'], args['y'], data['prmsl'], 
                                       'min', 80, symbol='L', color='coral', random=True)

        an_fc = utils.annotation_forecast(args['ax'], time)
        an_var = utils.annotation(args['ax'], 'MSLP [hPa] and temperature @850hPa [C]',
                            loc='lower left', fontsize=6)
        an_run = utils.annotation_run(args['ax'], run)
        an_run = utils.annotation_run(args['ax'], run)
        

        if first:
            plt.colorbar(cs, orientation='horizontal', label='Temperature', pad=0.03, fraction=0.04)

        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **utils.options_savefig)

        utils.remove_collections([c, cs, labels, an_fc, an_var, an_run, maxlabels, minlabels])

        first = False 

if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    utils.print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
