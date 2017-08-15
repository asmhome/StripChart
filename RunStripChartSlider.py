import StripChartSlider
#...............main program.............................
#create instance of StripChart            
chart1 = StripChartSlider.StripChart()
#open the port
port = 8889
chart1.opensock(port)
#set up channel names and complete setup
chart1.getnames()
#start chart animation and data collection over socket
chart1.runanimation()
