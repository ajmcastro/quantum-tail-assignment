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
    
    def test_can_perform_flight(self):
        
        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        flight0 = Flight(0,0,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('AMS')], 'NB', '01/09/2009 03:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        flight1 = Flight(1,1,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'WB', '01/09/2009 05:00', '01/09/2009 05:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        flight2 = Flight(2,2,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'NB', '01/09/2009 06:00', '01/09/2009 08:55', 15, 133, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        flight3 = Flight(3,3,540,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('DKR')], 'NB', '02/09/2009 06:30', '02/09/2009 08:55', 15, 133, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'DKR'))].distance, False)

        maintenance0 = Maintenance(4, 0, 'T2', '02/09/2009 06:00', '02/09/2009 07:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance0)
        aircraft0.add_overlap_flight(flight3)

        self.assertTrue(aircraft0.can_perform_flight(flight0))
        self.assertFalse(aircraft0.can_perform_flight(flight1))
        self.assertFalse(aircraft0.can_perform_flight(flight2))
        self.assertFalse(aircraft0.can_perform_flight(flight3))
    
    def test_group_maintenances(self):

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        maintenance0 = Maintenance(0, 0, 'T2', '01/09/2009 06:00', '01/09/2009 07:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance0)

        maintenance1 = Maintenance(1, 1, 'A', '01/09/2009 07:05', '01/09/2009 09:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance1)

        maintenance2 = Maintenance(2, 2, 'T2', '01/09/2009 06:30', '01/09/2009 07:30', self.airports[self.airports.index('FNC')], 'S', False)
        aircraft0.add_maintenance(maintenance2)

        maintenance3 = Maintenance(3, 3, 'T2', '02/09/2009 06:00', '02/09/2009 07:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance3)

        final_maint0 = Maintenance(0, 0, 'T2+A', '01/09/2009 06:00', '01/09/2009 09:00', self.airports[self.airports.index('LIS')], 'S', False)

        aircraft0.group_maintenances()

        self.assertTrue(len(aircraft0.maintenances) == 2)
        self.assertTrue(str(final_maint0.check_type_code) == str(aircraft0.maintenances[0].check_type_code))
        self.assertTrue(final_maint0.start_time == aircraft0.maintenances[0].start_time)
        self.assertTrue(final_maint0.end_time == aircraft0.maintenances[0].end_time)
    
    def test_maintenance_connections(self):

        aircraft0 = Aircraft(0, 'CSTTC', 'FERNANDO PESSOA', self.aircraft_models[self.aircraft_models.index('319')], 12, 126)

        flight0 = Flight(0,0,540,self.airports[self.airports.index('DKR')], self.airports[self.airports.index('LIS')], 'NB', '01/09/2009 00:00', '01/09/2009 05:00', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('DKR', 'LIS'))].distance, False)

        maintenance0 = Maintenance(1, 0, 'T2', '01/09/2009 06:00', '01/09/2009 07:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance0)

        maintenance1 = Maintenance(2, 1, 'A', '01/09/2009 09:05', '01/09/2009 10:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance1)

        flight1 = Flight(3,1,541,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('FNC')], 'NB', '01/09/2009 10:50', '01/09/2009 13:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        maintenance2 = Maintenance(4, 2, 'T2', '01/09/2009 18:30', '02/09/2009 07:30', self.airports[self.airports.index('FNC')], 'S', False)
        aircraft0.add_maintenance(maintenance2)

        flight2 = Flight(5,2,542,self.airports[self.airports.index('FNC')], self.airports[self.airports.index('LIS')], 'NB', '02/09/2009 8:50', '02/09/2009 10:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('FNC', 'LIS'))].distance, False)        

        maintenance3 = Maintenance(6, 3, 'T2', '02/09/2009 12:00', '02/09/2009 13:00', self.airports[self.airports.index('LIS')], 'S', False)
        aircraft0.add_maintenance(maintenance3)

        flight3 = Flight(7,3,543,self.airports[self.airports.index('LIS')], self.airports[self.airports.index('FNC')], 'NB', '02/09/2009 17:00', '02/09/2009 18:55', 15, 113, 8, 108, self.city_pairs[self.city_pairs.index(CityPair('LIS', 'AMS'))].distance, False)

        aircraft0.add_maintenance_connection_flight(flight0)
        aircraft0.add_maintenance_connection_flight(flight1)
        aircraft0.add_maintenance_connection_flight(flight2)
        aircraft0.add_maintenance_connection_flight(flight3)

        self.assertTrue(aircraft0.maintenances[0].prev_flights == [flight0] and len(aircraft0.maintenances[0].pos_flights) == 0)
        self.assertTrue(len(aircraft0.maintenances[1].prev_flights) == 0 and aircraft0.maintenances[1].pos_flights == [flight1])
        self.assertTrue(aircraft0.maintenances[2].prev_flights == [flight1] and aircraft0.maintenances[2].pos_flights == [flight2])
        self.assertTrue(aircraft0.maintenances[3].prev_flights == [flight2] and aircraft0.maintenances[3].pos_flights == [flight3]) 


if __name__ == "__main__":
    unittest.main()






