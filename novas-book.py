from datetime import datetime
import leapseconds              # from https://gist.github.com/zed/92df922103ac9deb1a05#file-leapseconds-py

from novas import compat as novas
from novas.compat import eph_manager
jd_start, jd_end, number = eph_manager.ephem_open()

(day, month, year) = (15, 3, 2021)
(planet_no, planet) = (4, 'Mars')

# Get number of leapseconds between TAI and UTC. This is used for calculating
# TT from UT1. TT = leapseconds + 32.184s + UT1. http://www.stjarnhimlen.se/comp/time.html
leapseconds = leapseconds.dTAI_UTC_from_utc(datetime(year, month, day)).seconds
#print leapseconds
delta_TT_UT1 = (32.184 + leapseconds) / 3600.0

print()
print ('    %s %d.%d.%d' % (planet, day, month, year))
print ()
print ('UT1     Grt            Dek            Frühlp.')
print ('      °   min         °   min         °   min')

for time_ut1 in range(24):
    time_tt = delta_TT_UT1 + time_ut1
    jd_tt = novas.julian_date(year, month, day, time_tt)
    jd_ut1 = novas.julian_date(year, month, day, time_ut1)
    theta = novas.sidereal_time(jd_ut1,0,delta_TT_UT1,1) * 360 / 24
    mars = novas.make_object(0, planet_no, planet, None)
    ra, dec, dis = novas.app_planet(jd_tt, mars)
    ra = ra * 360 / 24
    grt = theta - ra
    if grt < 0:
        grt = grt + 360.0
    print ('%02d   %03d  %04.1f      %04d  %04.1f       %03d  %04.1f' % (time_ut1, grt, abs(grt) % 1. * 60, dec, abs(dec) % 1. * 60., theta, abs(theta) % 1. * 60.))

