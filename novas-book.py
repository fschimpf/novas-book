from datetime import datetime
from leapseconds import dTAI_UTC_from_utc           # from https://gist.github.com/zed/92df922103ac9deb1a05#file-leapseconds-py

from novas import compat as novas
from novas.compat import eph_manager

import os

from datetime import date
from dateutil.rrule import rrule, DAILY

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

weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Sonnabend', 'Sonntag']
months = ['','Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

# It is not easy to find data for all stars from the same catalog. Wikipedia entries use different catalogs for the entries. Most important
# is that coordinats are referenced for Epoch J2000 and Equinox J2000.0 (ICRS). That is the case in Wikipedia. I used these entries. 
# Entries for catalog and catalog number are therefore left empty.
# tuple for stars: (no_in_Nautisches_Jahrbuch, novas-entry)
stars = [
    #                                                                                      motion       motion     prallax radial velocity
    #                             Name            Cat  No       Ra[h]        delta[deg]   Ra[mas/a]   Dec [mas/a] [mas]      [km/s]
    (1,  novas.make_cat_entry ("Alpha Andromedae",  "", 0,   0.139794411,  -29.09043111,   +135.68,    -162.95,      33.62,  -10.6)),
    (3,  novas.make_cat_entry ("Alpha Phoenicis",   "", 0,   0.438069833,  -42.30598719,   +233.05,    -356.3,       38.5,   +74.6)),
    (4,  novas.make_cat_entry ("Alpha Cassiopeiae", "", 0,   0.675122527,  +56.53733111,   +50.88,     -32.13,       14.29,  -4.31)),
    (5,  novas.make_cat_entry ("Beta Ceti",         "", 0,   0.726491916,  -17.98660631,   +232.55,    +31.99,       33.86,  +12.9)),
    (8,  novas.make_cat_entry ("Alpha Eridani",     "", 0,   1.628568189,  -57.23675281,   +87.00,     -38.24,       23.39,  +16.0)),
    (11, novas.make_cat_entry ("Alpha Arietis",     "", 0,   2.119557139,  +23.46241756,   +188.55,    -148.08,      49.56,  +14.2))
]

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

def calculate_ephemerides_planets_day (year, month, day):

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

        # calculate position of star
        if time_ut1 < len(stars):
            star_no, star = stars[time_ut1]
            ra, dec = novas.app_star(jd_tt, star) # FIX: Use fixed time in middle of 2-day-period instead. Star positions are valid for 2 days.
            sha = 360.0 - (ra * 360.0 / 24.0)  # Calculate sidereal hour angle (SHA) from right ascension and convert from hours to degrees.
            planet_results_per_UT1['stars'] = (star_no, decimal2dm_360(sha), decimal2dm_NS(dec))
        else:
            planet_results_per_UT1['stars'] = ('*', ('*', '*'), ('*', '*'))
        day_results.append(planet_results_per_UT1)

    return day_results


# Start Main...
# Open ephemerides database
jd_start, jd_end, number = eph_manager.ephem_open()

year = 2005
startdate = date(year, 3, 18)
enddate = date(year, 3, 21)

# Open Jinja-template-files for generating LaTex-document
document_template = jinja.get_template('NJ_mainDocument.tex.jinja')
table_eph_day_template = jinja.get_template('NJ_tableEphDay.tex.jinja')

# ut1 is used for iterating through list with results from within the Jinja-template 
ut1 = range(24)

table=''
page_is_even = 1

# For every day in book...
for dt in rrule(DAILY, dtstart=startdate, until=enddate):
    year = int(dt.strftime('%Y'))
    month = int(dt.strftime('%m'))
    day = int(dt.strftime('%d'))
    weekday = weekdays[dt.weekday()]
    print ('{}, {}.{}.{}'.format(weekday, day, month, year))

    # Calculate ephemerides for the selected day
    day_results = calculate_ephemerides_planets_day (year, month, day)

    #render day's results into (long) string
    table = table + table_eph_day_template.render(year=year, month=months[month], day=day, dayofweek=weekday, d=day_results, page_is_even=page_is_even, ut1=ut1)

    if page_is_even == 1:
        page_is_even = 0
    else:
        page_is_even = 1

# Open output file (LaTex)
dir_fd = os.open('./output', os.O_RDONLY)
def opener(path, flags):
    return os.open(path, flags, dir_fd=dir_fd)
outfile = open('Ephemeriden_{}.tex'.format(year), 'w', opener=opener)

# Render the main template and write to output-file
print(document_template.render(year=year,table=table),file=outfile)

outfile.close()

# Print something to shell 
print ('done')

# FIX: run pdflatex
#subprocess.run("pdflatex", "-synctex=1 -interaction=nonstopmode ./output/book.tex")