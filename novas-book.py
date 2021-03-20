from datetime import datetime
from leapseconds import dTAI_UTC_from_utc           # from https://gist.github.com/zed/92df922103ac9deb1a05#file-leapseconds-py

from novas import compat as novas
from novas.compat import eph_manager

import os

from jinja2 import Environment, FileSystemLoader
jinja = Environment(
    block_start_string = '((*',                     # Set delimiters to LaTex-conform strings
    block_end_string= '*))',
    variable_start_string= '(((',
    variable_end_string= ')))',
    comment_start_string= '((=',
    comment_end_string= '=))',
    line_statement_prefix= '###',
    loader=FileSystemLoader('templates')
)

# convert float to degrees and minutes, 'N' or 'S' instead of sign
def decimal2dm_NS (decimal_angle):
    if abs(decimal_angle) > 90:
        raise NameError('Invalid declination angle')

    # calculate minutes from fraction part
    min = round(abs(decimal_angle) % 1. * 60, 1)
    # add N or S instead of + or -
    if decimal_angle >= 0:
        min = '{:04.1F} N'.format(min)
    else:
        min = '{:04.1F} S'.format(min)
    
    # convert decimal part to string and remove sign and fraction part. (Important not to round, minutes are separeted!)
    deg = int(abs(decimal_angle))
    deg = '{:02.0F}'.format(deg)
    
    return (deg, min)

#convert float to degrees and minuts, full circle
def decimal2dm_360 (decimal_angle):
    if decimal_angle < 0:
        raise NameError('Invalid sign for full-circle-angle')
    
    # calculate minutes from fraction part
    min = round(abs(decimal_angle) % 1. * 60, 1)
    min = '{:04.1F}'.format(min)

    # convert decimal part to string and remove fraction part. (Important not to round, minutes are separeted!)
    deg = int(abs(decimal_angle))
    deg = '{:03.0F}'.format(deg)
    
    return (deg, min)

def calculate_ephemerides_planets_day (day, month, year):

    # define novas objects List of (novas_object, planet_name)
    sky_objects = []
    sky_objects.append((novas.make_object(0, 10, 'sun', None), 'sun'))
    sky_objects.append((novas.make_object(0, 11, 'moon', None), 'moon'))
    sky_objects.append((novas.make_object(0, 2, 'venus', None), 'venus'))
    sky_objects.append((novas.make_object(0, 4, 'mars', None), 'mars'))
    sky_objects.append((novas.make_object(0, 5, 'jupiter', None), 'jupiter'))
    sky_objects.append((novas.make_object(0, 6, 'saturn', None), 'saturn'))

    # Get number of leapseconds between TAI and UTC. This is used for calculating
    # TT from UT1. TT = leapseconds + 32.184s + UT1. http://www.stjarnhimlen.se/comp/time.html
    leapseconds = dTAI_UTC_from_utc(datetime(year, month, day)).seconds
    delta_TT_UT1 = (32.184 + leapseconds) / 3600.0

    day_results = []
    for time_ut1 in range(24): # iterate over 24h of UT1 (=lines in final table for one day)

        # calculate Julian date of TT and UT1 
        time_tt = delta_TT_UT1 + time_ut1
        jd_tt = novas.julian_date(year, month, day, time_tt)
        jd_ut1 = novas.julian_date(year, month, day, time_ut1)

        # calculate Greenwich hour angle (GHA) for spring point
        theta = novas.sidereal_time(jd_ut1,0,delta_TT_UT1,1) * 360 / 24
        planet_results_per_UT1 = {'spr_p': decimal2dm_360(theta)}

        # calculate Greenwich hour angle and declination for planets (sun and moon are considered planets)
        for (planet, planet_name) in sky_objects:
            ra, dec, dis = novas.app_planet(jd_tt, planet)
            ra = ra * 360.0 / 24.0  # go from hour angle to degrees
            grt = theta - ra    # calculate hour angle from GHA and planet's right ascension
            if grt < 0:
                grt = grt + 360.0
            planet_results_per_UT1[planet_name] = (decimal2dm_360(grt), decimal2dm_NS(dec))
        
        day_results.append(planet_results_per_UT1)

    return day_results


# Start Main...
# Open ephemerides database
jd_start, jd_end, number = eph_manager.ephem_open()

# Calculate ephemerides for one selected day
day_results = calculate_ephemerides_planets_day (12, 3, 2005)

# Open Jinja-template-file for generating LaTex-document
template = jinja.get_template('table_style_Nautisches_Jahrbuch.tex.jinja')

# Open output file (LaTex)
dir_fd = os.open('./output', os.O_RDONLY)
def opener(path, flags):
    return os.open(path, flags, dir_fd=dir_fd)
outfile = open('book.tex', 'w', opener=opener)

# ut1 is used for iterating through list with results from withing the Jinja-template 
ut1 = range(24)

# Render the template and write to output-file
print(template.render(year='2005', month='März', day='12', dayofweek='Samstag', d=day_results, ut1=ut1),file=outfile)

outfile.close()

# Print something to shell 
for time_ut1 in range(24):
    print (day_results[time_ut1])
    print ()

# FIX: run pdflatex
#subprocess.run("pdflatex", "-synctex=1 -interaction=nonstopmode ./output/book.tex")