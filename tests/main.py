import unittest
from CSP.test_fleet import TestSimpleTests as CSPFleetTests
from CSP.test_model import TestSimpleTests as CSPModelTests
from QUBO.test_fleet import TestSimpleTests as QUBOFleetTests

if __name__ == '__main__':

    test_classes_to_run = [CSPFleetTests, CSPModelTests, QUBOFleetTests]

    loader = unittest.TestLoader()

    suites_list = []
    for test_class in test_classes_to_run:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    big_suite = unittest.TestSuite(suites_list)

    runner = unittest.TextTestRunner()
    results = runner.run(big_suite)
