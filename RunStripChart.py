import StripChartMod
#...............main program.............................
#create instance of StripChart            
chart1 = StripChartMod.StripChart()
#set up channel names via text file
filename = 'ChannelNames.txt'
chart1.getnames(filename)
#finish setting up
chart1.finishsetup()
#open the port
port = 8889
chart1.opensock(port)
#start chart animation and data collection over socket
chart1.runanimation()
