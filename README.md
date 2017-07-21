# StripChart
StripChart
Initial Commit
StripChart.py and other supporting files uploaded this morning
Correct mis-spelled StripChart name.
Running suggestions:
All four files should be in same directory.  Start StripChart first, then launch DataSender.  If DataSender fails to open socket just run it again, it should connect.  This version of the sender has the 250 msec delay every 5000 data sets and it trashes some data not sent too.  You can comment out that section for smoother data flow.
DataChannel.txt and ChartData.bin provide StripChart with the names for the channel to expect.  ChartData.bin provides the binary data for sender to send.
