import unittest
from hrcsentinel import monitor_telemetry

class TestMakeShieldPlot(unittest.TestCase):
    def test_make_shield_plot(self):
        fig_save_directory = "test_figures"
        plot_start = "2022-01-01"
        plot_stop = "2022-01-02"
        result = monitor_telemetry.make_shield_plot(fig_save_directory, plot_start, plot_stop)
        self.assertEqual(result, True)

if __name__ == '__main__':
    unittest.main()