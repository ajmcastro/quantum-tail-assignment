import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../../src")
import unittest
from models.Activity import Activity, Flight, Maintenance
from models.CityPair import CityPair
from models.Aircraft import Aircraft
from Loader import read_airports, read_aircraft_models, read_city_pairs

class TestSimpleTests(unittest.TestCase):

    def setUp(self):
        self.airports = read_airports("data/final/")
        self.aircraft_models = read_aircraft_models("data/final/")
        self.city_pairs = read_city_pairs(self.airports, "data/final/")

    def test_lower_greater_activity(self):

        
        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        flight1 = Flight(1,1,541,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'NB', '01/09/2009 04:40', '01/09/2009 06:55', 15, 123, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        maintenance0 = Maintenance(2, 0, 'T2', '01/09/2009 06:00', '01/09/2009 07:00', self.airports[self.airports.index('LIS')], 'S', False)

        self.assertTrue(flight0 < flight1)
        self.assertTrue(flight0 < maintenance0)
        self.assertFalse(maintenance0 < flight1)
    
    def test_equal_activities(self):
        
        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        flight1 = Flight(1,1,541,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'NB', '01/09/2009 04:40', '01/09/2009 06:55', 15, 123, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        maintenance0 = Maintenance(2, 0, 'T2', '01/09/2009 06:00', '01/09/2009 07:00', self.airports[self.airports.index('LIS')], 'S', False)
               
        maintenance1 = Maintenance(3, 1, 'T2', '01/09/2009 08:00', '01/09/2009 09:00', self.airports[self.airports.index('LIS')], 'S', False)

        self.assertFalse(flight0 == flight1)
        self.assertFalse(flight1 == maintenance0)
        self.assertFalse(flight0 == maintenance0)
        self.assertFalse(maintenance0 == maintenance1)
        self.assertTrue(flight0 == flight0)
        self.assertTrue(maintenance0 == maintenance0)
    
    def test_check_overlap(self):
        
        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '02/09/2009 03:00', '02/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        flight1 = Flight(1,1,541,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'NB', '02/09/2009 04:40', '02/09/2009 06:55', 15, 123, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        flight2 = Flight(2,2,541,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'NB', '01/09/2009 04:40', '01/09/2009 06:55', 15, 123, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        maintenance0 = Maintenance(3, 0, 'T2', '01/09/2009 06:00', '03/09/2009 07:00', self.airports[self.airports.index('LIS')], 'S', False)
               
        maintenance1 = Maintenance(4, 1, 'T2', '02/09/2009 06:05', '02/09/2009 09:00', self.airports[self.airports.index('LIS')], 'S', False)

        # ---- maintenance_start, flight_start, flight_end, maintenance_end ----
        self.assertTrue(maintenance0.check_overlap(flight1))
        self.assertTrue(flight1.check_overlap(maintenance0))

        # ---- flight0_start, flight1_start, flight0_end, flight1_end ----
        self.assertTrue(flight0.check_overlap(flight1))
        self.assertTrue(flight1.check_overlap(flight0))

        # ---- overlap because rotation time: flight0_start, flight0_end, maintenance1_start, maintenance1_end ---
        self.assertTrue(flight0.check_overlap(maintenance1))
        self.assertTrue(maintenance1.check_overlap(flight0))

        # ---- no overlap ----
        self.assertFalse(flight0.check_overlap(flight2))
        self.assertFalse(flight2.check_overlap(flight0))
        self.assertFalse(maintenance1.check_overlap(flight2))
        self.assertFalse(flight2.check_overlap(maintenance1))

    def test_compatible_flight(self):


        
        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '02/09/2009 03:00', '02/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        flight1 = Flight(1,1,541,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'NB', '02/09/2009 04:40', '02/09/2009 06:55', 15, 123, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        flight2 = Flight(2,2,541,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'WB', '01/09/2009 04:40', '01/09/2009 06:55', 15, 123, 10, 113, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        maintenance0 = Maintenance(3, 0, 'T2', '01/09/2009 06:00', '03/09/2009 07:00', self.airports[self.airports.index('LIS')], 'S', False)

        self.assertTrue(flight0.compatible_flight(flight1))
        self.assertTrue(flight1.compatible_flight(flight0))
        self.assertTrue(flight0.compatible_flight(flight2))
        self.assertTrue(flight1.compatible_flight(flight2))
        self.assertRaises(NotImplementedError, maintenance0.compatible_flight, flight0)
        self.assertFalse(flight0.compatible_flight(maintenance0))


if __name__ == "__main__":
    unittest.main()
