from datetime import datetime
from leapseconds import dTAI_UTC_from_utc           # from https://gist.github.com/zed/92df922103ac9deb1a05#file-leapseconds-py

from novas import compat as novas
from novas.compat import eph_manager

import os
import sys

from datetime import date
from dateutil.rrule import rrule, DAILY

from math import atan, pi

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

weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
months = ['','Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

# It is not easy to find data for all stars from the same catalog. Wikipedia entries use different catalogs for the entries. Most important
# is that coordinats are referenced for Epoch J2000 and Equinox J2000.0 (ICRS). 
# Entries for catalog and catalog number are left empty.
# tuple for stars: (no_in_Nautisches_Jahrbuch, novas-entry)
stars = [
    #                                                                                      motion       motion     parallax radial velocity
    #                             Name            Cat  No       Ra[h]        delta[deg]   Ra[mas/a]   Dec [mas/a]  [mas]     [km/s]
    (1,  novas.make_cat_entry ("Alpha Andromedae",  "", 0,   0.139794444,  +29.09044444,   +135.68,    -162.95,      33.62,  -10.6)),
    (3,  novas.make_cat_entry ("Alpha Phoenicis",   "", 0,   0.438069833,  -42.30598719,   +233.05,    -356.3,       38.5,   +74.6)),
    (4,  novas.make_cat_entry ("Alpha Cassiopeiae", "", 0,   0.675122527,  +56.53733111,   +50.88,     -32.13,       14.29,  -4.31)),
    (5,  novas.make_cat_entry ("Beta Ceti",         "", 0,   0.726491916,  -17.98660631,   +232.55,    +31.99,       33.86,  +12.9)),
    (8,  novas.make_cat_entry ("Alpha Eridani",     "", 0,   1.628568189,  -57.23675281,   +87.00,     -38.24,       23.39,  +16.0)),
    (11, novas.make_cat_entry ("Alpha Arietis",     "", 0,   2.119557139,  +23.46241756,   +188.55,    -148.08,      49.56,  +14.2))
]


# define novas objects List of (novas_object, planet_name)
sky_objects = []
sky_objects.append((novas.make_object(0, 10, 'sun', None), 'sun'))
sky_objects.append((novas.make_object(0, 11, 'moon', None), 'moon'))
sky_objects.append((novas.make_object(0, 2, 'venus', None), 'venus'))
sky_objects.append((novas.make_object(0, 4, 'mars', None), 'mars'))
sky_objects.append((novas.make_object(0, 5, 'jupiter', None), 'jupiter'))
sky_objects.append((novas.make_object(0, 6, 'saturn', None), 'saturn'))

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
    
    min = min.replace('.',',')      # replace '.' by ',' FIX?: Locale-dependent

    # convert decimal part to string and remove sign and fraction part. (Important not to round, minutes are separeted!)
    deg = int(abs(decimal_angle))
    deg = '{:02.0F}'.format(deg)
    
    return (deg, min)

#convert float to degrees and minutes, full circle
def decimal2dm_360 (decimal_angle):
    if decimal_angle < 0:
        raise NameError('Invalid sign for full-circle-angle')
    
    # calculate minutes from fraction part
    min = round(abs(decimal_angle) % 1. * 60, 1)
    min = '{:04.1F}'.format(min)
    min = min.replace('.',',')  # replace '.' by ','  FIX?: Locale-dependent

    # convert decimal part to string and remove fraction part. (Important not to round, minutes are separeted!)
    deg = int(abs(decimal_angle))
    deg = '{:03.0F}'.format(deg)
    
    return (deg, min)

#convert float to minutes, with sign
def decimal2min (decimal_angle):
    if abs(decimal_angle) >= 1.0:
        raise NameError('Angle larger than 1.0. Conversion to minutes failed.')
    
    # calculate minutes from fraction part
    min = round(decimal_angle * 60, 1)
    min = '{:-5.1F}'.format(min)
    min = min.replace('.',',')  # replace '.' by ','  FIX?: Locale-dependent
    
    return min

#convert float to hours and minutes
def decimal2hm (decimal_angle):
    if decimal_angle < 0:
        raise NameError('Invalid sign for time')
    
    # calculate minutes from fraction part
    min = round(abs(decimal_angle) % 1. * 60, 0)
    min = '{:02.0F}'.format(min)
    
    # convert decimal part to string and remove fraction part. (Important not to round, minutes are separeted!)
    deg = int(abs(decimal_angle))
    deg = '{:02.0F}'.format(deg)
    
    return (deg, min)

#convert float to only minutes with sign
def decimal2m (decimal_angle):
    #if abs(decimal_angle) > 1.0:
    #    raise NameError('Angle too large for converting to only minutes')
    
    # calculate minutes from fraction part
    min = round(abs(decimal_angle) * 60, 1)
    if decimal_angle < 0:
        min = 0 - min 
    min = '{:-3.1F}'.format(min)
    
    min = min.replace('.',',')  # replace '.' by ','  FIX?: Locale-dependent
    return min

# Calculates transit time within tolerance of 10 s. Transit must lie between jd_ut1_left and jd_ut1_right. Return value is in hours. 
def calculate_transit_spring_point (year, month, day, jd_ut1_left, jd_ut1_right, delta_TT_UT1):
    delta_ut1 = jd_ut1_right - jd_ut1_left
    if delta_ut1 > 0.00011574:   # If tolerance greater than 10 s (10s expressed in days)
        jd_ut1_middle = jd_ut1_left + (delta_ut1 / 2.0)        # choose new time in the middle between jd_ut1_left and jd_ut1_right
        theta_left = novas.sidereal_time(jd_ut1_left,0,delta_TT_UT1,1) * 360 / 24 # calculate theta for left side
        theta_middle = novas.sidereal_time(jd_ut1_middle,0,delta_TT_UT1,1) * 360 / 24 # calculate theta for middle
        if theta_left < theta_middle:  # normal increase of angle, transit must be on right side of middle
            transit_time = calculate_transit_spring_point (year, month, day, jd_ut1_middle, jd_ut1_right, delta_TT_UT1)    # recursively find transit betw. middle and right
        else:
            transit_time = calculate_transit_spring_point (year, month, day, jd_ut1_left, jd_ut1_middle, delta_TT_UT1)    # recursively find transit betw. left and middle
    else:   # Tolerance fulfilled, find time and return
        jd_ut1 = novas.julian_date(year, month, day, 0)     # Calculate Julian date for 0:00 this day.
        transit_time = (jd_ut1_right - jd_ut1) * 24.0         # Difference is transit time in days. *24 = transit time in hours
        #print ('recursion finished. Transit: ', transit_time)

    return transit_time

def calculate_grt_planet (jd_tt, theta, planet):
        ra, dec, dis = novas.app_planet(jd_tt, planet)
        ra = ra * 360.0 / 24.0  # go from hour angle to degrees
        grt = theta - ra    # calculate hour angle from GHA and planet's right ascension
        if grt < 0:
            grt = grt + 360.0
        return grt

# Calculates transit time within tolerance of 10 s. Transit must lie between jd_ut1_left and jd_ut1_right. Return value is in hours. 
def calculate_transit_planet (year, month, day, jd_ut1_left, jd_ut1_right, delta_TT_UT1, planet):
    delta_ut1 = jd_ut1_right - jd_ut1_left
    if delta_ut1 > 0.00011574:   # If tolerance greater than 10 s (10s expressed in days)
        jd_ut1_middle = jd_ut1_left + (delta_ut1 / 2.0)        # choose new time in the middle between jd_ut1_left and jd_ut1_right
        theta_left = novas.sidereal_time(jd_ut1_left,0,delta_TT_UT1,1) * 360 / 24 # calculate theta for left side
        theta_middle = novas.sidereal_time(jd_ut1_middle,0,delta_TT_UT1,1) * 360 / 24 # calculate theta for middle

        # calculate Julian dates in TT 
        jd_tt_left = jd_ut1_left + (delta_TT_UT1 / 86400.0)     # add delta_TT_UT1 in days FIX: Is precision sufficient?
        jd_tt_middle = jd_ut1_middle + (delta_TT_UT1 / 86400.0) # add delta_TT_UT1 in days FIX: Is precision sufficient?

        # calculate planets GRT        
        grt_left = calculate_grt_planet (jd_tt_left, theta_left, planet)
        grt_middle = calculate_grt_planet (jd_tt_middle, theta_middle, planet)

        if grt_left < grt_middle:  # normal increase of angle, transit must be on right side of middle
            transit_time = calculate_transit_planet (year, month, day, jd_ut1_middle, jd_ut1_right, delta_TT_UT1, planet)    # recursively find transit betw. middle and right
        else:
            transit_time = calculate_transit_planet (year, month, day, jd_ut1_left, jd_ut1_middle, delta_TT_UT1, planet)    # recursively find transit betw. left and middle

    else:   # Tolerance fulfilled, find time and return transit time
        jd_ut1 = novas.julian_date(year, month, day, 0)     # Calculate Julian date for 0:00 this day.
        
        transit_time = (jd_ut1_right - jd_ut1) * 24.0         # Difference is transit time in days. *24 = transit time in hours
        #print ('recursion finished. Transit: ', transit_time)

    return transit_time

# Find average differences over one day for use in interpolation/correction tables (valid for planetes and sun)
# returns GHA difference and dec-difference in minutes.
def calculate_avg_differences (jd_ut1, delta_TT_UT1, planet):
    jd_tt = jd_ut1 + (delta_TT_UT1 / 86400.0)     # add delta_TT_UT1 in days FIX: Is precision sufficient?
    theta_start = novas.sidereal_time(jd_ut1,0,delta_TT_UT1,1) * 360 / 24
    ra, dec_start, dis = novas.app_planet(jd_tt, planet)
    ra = ra * 360.0 / 24.0  # go from hour angle to degrees
    grt_start = theta_start - ra    # calculate hour angle from GHA and planet's right ascension
    if grt_start < 0:
        grt_start = grt_start + 360.0

    jd_tt_end = jd_ut1 + 1.0 + (delta_TT_UT1 / 86400.0)     # add delta_TT_UT1 in days FIX: Is precision sufficient?
    theta_end = novas.sidereal_time(jd_ut1 + 1.0 ,0,delta_TT_UT1,1) * 360 / 24
    ra, dec_end, dis = novas.app_planet(jd_tt_end, planet)
    ra = ra * 360.0 / 24.0  # go from hour angle to degrees
    grt_end = theta_end - ra    # calculate hour angle from GHA and planet's right ascension
    if grt_end < 0:
        grt_end = grt_end + 360.0

    d_grt = (grt_end - grt_start)
    if d_grt > 360.0:
        d_grt = d_grt - 360.0
    d_grt_hourly = d_grt / 24.0   # calculate average hourly difference and subtract average sideral change of GRT.
    d_grt = decimal2m(d_grt_hourly)   # convert to string and take only minutes

    d_dec = (dec_end - dec_start) / 24.0
    d_dec = decimal2m(d_dec)   # convert to string and take only minutes

    return d_grt, d_dec
    

    
def horizontal_parallaxe (distance):      # calculates horizontal parallaxe for body with given distance from earth (unit: AU). Returns HP in arcminutes
    hp = atan(0.0000426343 / distance) * 360 / (2 * pi)  # HP in degrees = atan (earth_raduis[AU] / distance [AU])
    hp_minutes = decimal2m(hp)              # expected result is smaller than 1 degree, take only minutes part.
    return hp_minutes

def calculate_ephemerides_day (year, month, day):

    # Get number of leapseconds between TAI and UTC. This is used for calculating
    # TT from UT1. TT = leapseconds + 32.184s + UT1. http://www.stjarnhimlen.se/comp/time.html
    leapseconds = dTAI_UTC_from_utc(datetime(year, month, day)).seconds
    delta_TT_UT1 = (32.184 + leapseconds) / 3600.0  # time difference in hours

    # Calculate Julian Date for stars. The star-data changes slowly and is always used for two day in the final tables. 
    # Therefore the time is chosen to be in the middle of such a 2-day-period.
    # DIRTY: Just added 23.5 h the Gregorian date.
    # FIX: Do something with the second double-page. 
    jd_tt_stars = novas.julian_date(year, month, day, delta_TT_UT1 + 23.5)

    planets = []
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
            if planet_name == 'moon':    # Moon needs some more data:
                #Calculation of differences to the next hour
                # Difference to NJ: Difference is given with sign. NJ gives it without sign for moon.
                # NJ makes rounding errors. This calculation uses higher precision all the way until conversion to string.
                # Differences of +/- 0.1 min to NJ may occur.
                ra_next, dec_next, dis_next = novas.app_planet(jd_tt + 0.041666666, planet) # Positions for jd + 1 h
                theta_next = novas.sidereal_time(jd_ut1 + 0.041666666,0,delta_TT_UT1,1) * 360 / 24
                ra_next = ra_next * 360.0 / 24.0  # go from hour angle to degrees
                grt_next = theta_next - ra_next    # calculate hour angle from GHA and planet's right ascension
                if grt_next < 0:
                    grt_next = grt_next + 360.0

                 # Calculate hourly declination difference in minutes and convert to string.
                dec_diff_min = decimal2min(dec_next - dec)  

                # Calculate hourly GRT-difference and subtract "average" hourly difference used for interpolation tables
                # and convert to minutes and to string.
                grt_diff_min = (abs(grt_next) - abs(grt) - 14.31666667)
                if grt_diff_min < 0:
                    grt_diff_min += 360.0
                grt_diff_min = decimal2min(grt_diff_min)
                planet_results_per_UT1[planet_name] = (decimal2dm_360(grt), decimal2dm_NS(dec), grt_diff_min, dec_diff_min)

                # Get horizontal parallaxe at UT1 = 4, 12, 20
                if time_ut1 in [4, 12, 20]:
                    planet_results_per_UT1['hp_moon'] = horizontal_parallaxe (dis)

            else:                       # "Normal" planet:
                planet_results_per_UT1[planet_name] = (decimal2dm_360(grt), decimal2dm_NS(dec))

        # calculate position of star
        if time_ut1 < len(stars):
            star_no, star = stars[time_ut1]
            ra, dec = novas.app_star(jd_tt_stars, star) # FIX: Use fixed time in middle of 2-day-period instead. Star positions are valid for 2 days.
            sha = 360.0 - (ra * 360.0 / 24.0)  # Calculate sidereal hour angle (SHA) from right ascension and convert from hours to degrees.
            planet_results_per_UT1['stars'] = (star_no, decimal2dm_360(sha), decimal2dm_NS(dec))
        else:
            planet_results_per_UT1['stars'] = ('*', ('*', '*'), ('*', '*'))
        
        planets.append(planet_results_per_UT1)

    # Calculate transit time for spring point
    jd_ut1 = novas.julian_date(year, month, day, 0.0) # Start for possible transit 00:00 h that day, end + 1 day
    transits = {'spr_p': decimal2hm(calculate_transit_spring_point (year, month, day, jd_ut1, jd_ut1 + 1.0, delta_TT_UT1))}
    #print ('Transit spring point: {}:{}'.format(transits['spr_p'][0], transits['spr_p'][1]))

    # Transit times for planets, average differences and horizontal parallaxe
    for (planet, planet_name) in sky_objects:
        jd_ut1 = novas.julian_date(year, month, day, 0.0) # Start for possible transit 00:00 h that day, end + 1 day
        transits[planet_name] = decimal2hm(calculate_transit_planet (year, month, day, jd_ut1, jd_ut1 + 1.0, delta_TT_UT1, planet))
        if planet_name != 'moon': 
            transits['diff_' + planet_name] = calculate_avg_differences (jd_ut1, delta_TT_UT1, planet)
            ra, dec, dis = novas.app_planet(jd_ut1 + 0.5, planet)   # use "middle of day" for finding parallaxe
            transits['hp_' + planet_name] = horizontal_parallaxe (dis)
            #print ('HP {}: {}'.format(planet_name, transits['hp_' + planet_name]))
            if planet_name == 'sun':
                transits['r_sun'] = decimal2m(atan(0.00465476/dis) * 360 / (2 * pi))
                #print('Sonnenradius: {}'.format(transits['r_sun']))
        else: # moon, find days since new moon
            time_tt = delta_TT_UT1 + 0.0    # ut1 = 0h 
            jd_tt = novas.julian_date(year, month, day, time_tt)
            jd_ut1 = novas.julian_date(year, month, day, time_ut1)
            theta = novas.sidereal_time(jd_ut1,0,delta_TT_UT1,1) * 360 / 24
            ra, dec, dis = novas.app_planet(jd_tt, planet)
            ra = ra * 360.0 / 24.0  # go from hour angle to degrees
            grt = theta - ra    # calculate hour angle from GHA and planet's right ascension
            if grt < 0:
                grt = grt + 360.0

            transits['age_moon'] = 'x,y'
    return planets, transits


# Start Main...
# Open ephemerides database
jd_start, jd_end, number = eph_manager.ephem_open()

try:
    year = int(sys.argv[1])
except ValueError:
    print ('Error: No year given. Usage: novas-book.py <year to calculate>')
    sys.exit(2)

if (year < 1960) or (year > 2100):
    print ('Error: Invalid year. Valid range for year: 1950..2100')
    sys.exit(2)

startdate = date(year, 1, 1)
enddate = date(year, 12, 31)

# Open Jinja-template-files for generating LaTex-document
document_template = jinja.get_template('NJ_mainDocument.jinja.tex')
table_eph_day_template = jinja.get_template('NJ_tableEphDay.jinja.tex')

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
    time_tuple = dt.timetuple()
    additional_data = {'dayOfYear': time_tuple[7]}
    print ('calculating page for {}, {}.{}.{}'.format(weekday, day, month, year))

    # Calculate ephemerides for the selected day
    planets, transits = calculate_ephemerides_day (year, month, day)

    #render day's results into (long) string
    table = table + table_eph_day_template.render(year=year, month=months[month], day=day, dayofweek=weekday, d=planets, page_is_even=page_is_even, ut1=ut1, add=additional_data, transits=transits)

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