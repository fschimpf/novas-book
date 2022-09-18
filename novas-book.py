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
    #                                                                                                     motion       motion     parallax radial velocity
    #                               Name                            Cat  No     Ra[h]        Dec[deg]    Ra[mas/a]   Dec [mas/a]    [mas]    [km/s]
    (1,  novas.make_cat_entry ("Alpha Andromedae (Alpheratz)    ", "", 0,   0.139794444,  +29.09044444,   +135.68,    -162.95,      33.62,  -10.6)),
    (3,  novas.make_cat_entry ("Alpha Phoenicis                 ", "", 0,   0.438069833,  -42.30598719,   +233.05,    -356.3,       38.5,   +74.6)),
    (4,  novas.make_cat_entry ("Alpha Cassiopeiae (Schedir)     ", "", 0,   0.675122527,  +56.53733111,   +50.88,     -32.13,       14.29,  -4.31)),
    (5,  novas.make_cat_entry ("Beta Ceti (Deneb Kaitos)        ", "", 0,   0.726491916,  -17.98660631,   +232.55,    +31.99,       33.86,  +12.9)),
    (8,  novas.make_cat_entry ("Alpha Eridani (Achernar)        ", "", 0,   1.628568189,  -57.23675281,   +87.00,     -38.24,       23.39,  +16.0)),
    (11, novas.make_cat_entry ("Alpha Arietis (Hamal)           ", "", 0,   2.119557139,  +23.46241756,   +188.55,    -148.08,      49.56,  +14.2)),
    (12, novas.make_cat_entry ("Alpha Ceti (Menkar)             ", "", 0,   3.037991667,  +4.08975,       -10.41,     -76.85,       13.09,  -26.08)),
    (14, novas.make_cat_entry ("Alpha Persei (Mirfak)           ", "", 0,   3.405380556,  +49.86119444,   +23.75,     -26.23,       6.44,   -2.0)),
    (16, novas.make_cat_entry ("Alpha Tauri (Aldebaran)         ", "", 0,   4.598677778,  +16.50930556,   +63.45,     -188.94,      48.94,  +54.2)),
    (17, novas.make_cat_entry ("Beta Orionis (Rigel)            ", "", 0,   5.242305556,  -8.203611111,   +1.87,      -0.56,        3.2352, +25.0)),
    (18, novas.make_cat_entry ("Alpha Aurigae (Capella)         ", "", 0,   5.278152778,  +45.998,        +75.52,     -427.11,      76.2,   +29.9)),
    (19, novas.make_cat_entry ("Gamma Orionis (Bellatrix)       ", "", 0,   5.41885,      +6.349694444,   -8.11,      -12.88,       12.92,  +18.2)),
    (24, novas.make_cat_entry ("Alpha Orionis (Beteigeuze)      ", "", 0,   5.919530556,  +7.407055556,   +27.54,     +11.30,       5.95,   +21.9)),
    (27, novas.make_cat_entry ("Alpha Carinae (Canopus)         ", "", 0,   6.399197222,  -52.69566667,   +19.93,     +23.24,       10.55,  +20.3)),
    (29, novas.make_cat_entry ("Alpha Canis Majoris (Sirius)    ", "", 0,   6.752472222,  -16.71611667,   -546.01,    -1223.07,     379.21, -5.50)),
    (30, novas.make_cat_entry ("Epsilon Canis Majoris (Adhara)  ", "", 0,   6.977111111,  -28.97194444,   +2.63,      +2.29,        7.57,   +27.3)),
    (33, novas.make_cat_entry ("Alpha Canis Minoris (Procyon)   ", "", 0,   7.655033194,  +5.225,         -714.59,    -1036.8,      284.56, -3.2)),
    (34, novas.make_cat_entry ("Beta Geminorum (Pollux)         ", "", 0,   7.755263853,  +28.02619889,   -626.55,    -45.8,        96.54,  +3.23)),
    (35, novas.make_cat_entry ("Epsilon Carinae (Avior)         ", "", 0,   8.375277778,  -59.50944444,   -25.5,      +22.1,        5.39,   +11.6)),
    (36, novas.make_cat_entry ("Lambda Verlorum (Alsuhail)      ", "", 0,   9.133266667,  -43.43258333,   -24.01,     +13.52,       5.99,   +17.6)),
    (37, novas.make_cat_entry ("Beta Carinae (Miaplacidus)      ", "", 0,   9.219994444,  -69.71722222,   -156.47,    +108.95,      28.82,  -5.1)),
    (38, novas.make_cat_entry ("Alpha Hydrae (Alphard)          ", "", 0,   9.459788889,  -8.658611111,   -15.23,     +34.37,       18.09,  -4.7)),
    (39, novas.make_cat_entry ("Alpha Leonis (Regulus)          ", "", 0,   10.13953056,  +11.96722222,   -248.73,    +5.59,        41.13,  +5.9)),
    (41, novas.make_cat_entry ("Alpha Ursae majoris (Dubhe)     ", "", 0,   11.06213889,  +61.75111111,   -134.11,    -34.70,       26.54,  -9.4)),
    (42, novas.make_cat_entry ("Beta Leonis (Denebola)          ", "", 0,   11.81766111,  +14.57205556,   -497.68,    -114.76,      90.91,  -0.2)),
    (43, novas.make_cat_entry ("Alpha Crucis (Acrux)            ", "", 0,   12.44330556,  -63.09908333,   -35.83,     -14.86,       10.17,  -11.2)),
    (44, novas.make_cat_entry ("Gamma Crucis (Gacrux)           ", "", 0,   12.51943333,  -57.11321333,   +28.23,     -265.08,      36.83,  +20.6)),
    (46, novas.make_cat_entry ("Epsilon Ursae majoris (Alioth)  ", "", 0,   12.90048611,  +55.95983333,   +111.91,    -8.24,        39.51,  -12.7)),
    (49, novas.make_cat_entry ("Alpha Virginis (Spica)          ", "", 0,   13.41988889,  -11.16133333,   -42.35,     -30.67,       13.06,  +1.0)),
    (50, novas.make_cat_entry ("Eta Ursae majoris (Benetnasch)  ", "", 0,   13.79234444,  +49.31327778,   -121.17,    -14.91,       31.38,  -13.4)),
    (51, novas.make_cat_entry ("Beta Centauri (Agena)           ", "", 0,   14.06372222,  -60.37305556,   -33.27,     -23.16,       8.32,   +9.59)),
    (53, novas.make_cat_entry ("Alpha Bootis (Arcturus)         ", "", 0,   14.26101944,  +19.18241667,   -1093.39,   -2000.06,     88.83,  -5.2)),
    (54, novas.make_cat_entry ("Alpha Centauri (Toliman)        ", "", 0,   14.66013889,  -60.833975,     -3678.19,   +481.85,      737.0,  -22.3)),
    (56, novas.make_cat_entry ("Alpha Librae (Zubenelgenubi)    ", "", 0,   14.84797222,  -16.04166667,   -105.68,    -68.4,        43.03,  -23.47)),
    (57, novas.make_cat_entry ("Beta Ursae minoris (Kochab)     ", "", 0,   14.84509167,  +74.1555,       -32.61,     +11.42,       24.91,  +16.9)),
    (59, novas.make_cat_entry ("Alpha Corona Borealis (Alphecca)", "", 0,   15.57813889,  +26.71469444,   +120.27,    -89.58,       43.46,  +1.7)),
    (61, novas.make_cat_entry ("Alpha Scorpii (Antares)         ", "", 0,   16.49012806,  -26.43200278,   -10.16,     -23.21,       5.4,    -3.4)),
    (62, novas.make_cat_entry ("Alpha Trinanguli australis (Atria)", "", 0, 16.81108333,  -69.02772222,   +17.99,     -31.58,       8.35,   -3.0)),
    (64, novas.make_cat_entry ("Lambda Scorpii (Shaula)         ", "", 0,   17.56013889,  -37.10388889,   -8.53,      -30.80,       5.71,   -3.0)),
    (65, novas.make_cat_entry ("Alpha Ophiuchi (Ras Alhague)    ", "", 0,   17.58224167,  +12.56002778,   +108.07,    -221.57,      67.13,  +11.7)),
    (67, novas.make_cat_entry ("Gamma Draconis (Eltanin)        ", "", 0,   17.94344444,  +51.48888889,   -8.48,      -22.79,       21.14,  -28.0)),
    (68, novas.make_cat_entry ("Epsilon Sagitarii (Kau Australis)", "", 0,  18.40286111,  -34.38472222,   -39.42,     -124.2,       22.76,  -15.0)),
    (69, novas.make_cat_entry ("Alpha Lyrae (Wega)              ", "", 0,   18.61565,     +38.78369444,   +200.94,    +286.23,      130.23, -20.6)),
    (71, novas.make_cat_entry ("Alpha Aquilae (Atair)           ", "", 0,   19.84638889,  +8.868333333,   +536.23,    +385.29,      194.95, -26.6)),
    (72, novas.make_cat_entry ("Alpha Pavonis (Peacock)         ", "", 0,   20.42746111,  -56.73508333,   +6.9,       -86.02,       18.24,  +2.0)),
    (73, novas.make_cat_entry ("Alpha Cygni (Deneb)             ", "", 0,   20.69053194,  +45.28033889,   +1.56,      +1.55,        2.31,   -4.9)),
    (75, novas.make_cat_entry ("Epsilon Pegasi (Enif)           ", "", 0,   21.73643333,  +9.875,         +26.92,     +0.44,        4.73,   +3.4)),
    (76, novas.make_cat_entry ("Alpha Gruis (Al Nair)           ", "", 0,   22.13721944,  -46.96097222,   +128.0,     -148.0,       32.16,  +11.8)),
    (78, novas.make_cat_entry ("Alpha Piscis autralis (Formalhaut)", "", 0, 22.96084722,  -29.62225,      +328.95,    -164.67,      129.81, +6.5)),
    (80, novas.make_cat_entry ("Alpha Pegasi (Markab)           ", "", 0,   23.07936111,  +15.20527778,   +60.4,      -41.3,        24.46,  -2.7))
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