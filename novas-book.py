from datetime import datetime
from leapseconds import dTAI_UTC_from_utc           # from https://gist.github.com/zed/92df922103ac9deb1a05#file-leapseconds-py

from novas import compat as novas
from novas.compat import eph_manager

import os

from jinja2 import Environment, PackageLoader
jinja = Environment(
    block_start_string = '((*',                     # Set delimiters to LaTex-conform strings
    block_end_string= '*))',
    variable_start_string= '(((',
    variable_end_string= ')))',
    comment_start_string= '((=',
    comment_end_string= '=))',
    loader=PackageLoader('novas-book', 'templates')
)

jd_start, jd_end, number = eph_manager.ephem_open()

def calculate_ephemerides_planets_day (day, month, year):
    sky_object_names = [
        (10, 'Sonne'),
        (11, 'Mond'),
        (2, 'Venus'),
        (4, 'Mars'),
        (5, 'Jupiter'),
        (6, 'Saturn')
    ]
    sky_objects = []
    for i in sky_object_names:
        (planet_no, planet) = i
        #print (planet_no, planet)
        sky_objects.append(novas.make_object(0, planet_no, planet, None))

    # Get number of leapseconds between TAI and UTC. This is used for calculating
    # TT from UT1. TT = leapseconds + 32.184s + UT1. http://www.stjarnhimlen.se/comp/time.html
    leapseconds = dTAI_UTC_from_utc(datetime(year, month, day)).seconds
    delta_TT_UT1 = (32.184 + leapseconds) / 3600.0

    day_results = []
    for time_ut1 in range(24): # iterate over 24h of UT1 (=lines in final table for one day)
        planet_results_per_UT1 = []

        # calculate Julian date of TT and UT1 
        time_tt = delta_TT_UT1 + time_ut1
        jd_tt = novas.julian_date(year, month, day, time_tt)
        jd_ut1 = novas.julian_date(year, month, day, time_ut1)

        # calculate Greenwich hour angle (GHA) for spring point
        theta = novas.sidereal_time(jd_ut1,0,delta_TT_UT1,1) * 360 / 24
        planet_results_per_UT1.append((theta))

        # calculate Greenwich hour angle and declination for planets (sun and moon are considered planets)
        for planet in sky_objects:
            ra, dec, dis = novas.app_planet(jd_tt, planet)
            ra = ra * 360 / 24  # go from hour angle to degrees
            grt = theta - ra    # calculate hour angle from GHA and planet's right ascension
            if grt < 0:
                grt = grt + 360.0
            planet_results_per_UT1.append((grt, dec))
        
        day_results.append(planet_results_per_UT1)

    print (day_results)

calculate_ephemerides_planets_day (15, 3, 2021)

# Write the results into template-file
template = jinja.get_template('table_style_Nautisches_Jahrbuch.tex.jinja')

dir_fd = os.open('./output', os.O_RDONLY)
def opener(path, flags):
    return os.open(path, flags, dir_fd=dir_fd)
outfile = open('book.tex', 'w', opener=opener)
print(template.render(year='2021', month='Mai', day='13', dayofweek='Montag'),file=outfile)
outfile.close()

# FIX: run pdflatex
#subprocess.run("pdflatex", "-synctex=1 -interaction=nonstopmode ./output/book.tex")