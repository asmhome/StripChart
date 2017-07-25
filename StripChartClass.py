from Tkinter import*
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.animation as animation
import socket
import struct
import time
import datetime

class StripChart:
    def __init__(self):
        #...........DEMO ONLY.....text file with channel names
        self.filename = ''
        #max number of data sets to chart, 25 minutes @ 256usec
        self.datalimits = 6000000
        #get channel names
        #self.getnames()
        #default port number
        #self.port = 8889
        #self.opensock()
        #approximate period of time between data sets...only used to estimate chartwidth and other pre-sets
        self.timescale = 0.000256 #seconds
        #datafreq is frequency of data sets in hz
        self.datafreq = int(round(1/self.timescale,-3))
        #self.initialchartwidth is number of data sets displayed on the chart
        self.initialchartwidth = 3*self.datafreq  #approximately 3 seconds of data 3*round(1/self.timescale,-3)
        #chartwith is number of data set display after zooming
        self.chartwidth = self.initialchartwidth
        #self.displayinc is increment of number of points display moves each animation
        self.displayinc = int(self.initialchartwidth/6)
        #startself.displayinc holds original value of self.displayinc, self.displayinc can be modified by zuum function
        self.startdisplayinc = self.displayinc
        #self.dinc is number of data points read each animation step
        self.dinc = int(self.datafreq/2)  #approx 1/2 second of data or round(1/self.timescale,-3)/2
        #refreshrate controls rate of animation in milliseconds
        self.refreshrate = self.dinc/4  #every 1/2 second
        #used to clip data to fit chartwidth
        #displaymin is lowest data set NUMBER, not tdata value to be displayed
        self.displaymin =0
        #displaymmax is highes data set NUMBER, not tdata value to be displayed
        self.displaymax = 0
        #limit of data set that can be received
        self.tdata = [0 for x in range(self.datalimits)]
        #maximum value of tdata recieved
        self.tmax =0
        #maximum number of data sets recieved
        self.dmax =0
        #self.zuum is percent of chart zoom
        self.zuum = 100
        #counter for data sets recieved so far
        self.dcount =0
        #End of Data Flag - Set to 0, if Set to 1 = No More Data Coming
        self.eodflag = '0'
        #Feedback message to display for events like button pushed
        self.messagetext =''
        #message counter, allows messagetext to linger so user can read it before it is erased
        self.mcount = 0
        #strings used in text box 
        self.maxstr =''
        self.minstr=''
        self.tmaxstr=''
        self.tminstr=''




    def runanimation(self):

        #interval = refreshrate = time in milliseconds each animation cycle
        #note:  number of data set read each interval is set by 'self.dinc' variable    
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=self.refreshrate)
        #Tkinter mainloop, require to show window
        self.root.mainloop()


    #gets channel names and setup balance of variables....
    def getnames(self,filename):
        #..........This is a demo solution...actual channel names may be pass in a different way....
        with open(filename, 'r') as namesfile:
            #read channel self.names from file as string
            namedata=namesfile.read()
            #parse into a list
            self.names = namedata.strip().split(',')
            #..............................................end demo solution for channel names.....


            #the balance of setup depends on number of channels...so it is included here.......
            #number of channel is number of items in list
            self.numchannel = len(self.names)
            #create array for actual data and fill with 0's
            self.channeldata = [[0 for x in range(self.datalimits)] for y in range(self.numchannel)]
            #array of zeros used to hold min & max channel data with TOF
            self.minchannel = [0 for x in range(self.numchannel)]
            self.tminchannel = [0 for x in range(self.numchannel)]
            self.maxchannel = [0 for x in range(self.numchannel)]
            self.tmaxchannel = [0 for x in range(self.numchannel)]
            #pre-set min max values
            for i in range(0,self.numchannel):    
                self.minchannel[i] = 1000000.0
                self.maxchannel[i] = -1000000.0
                self.tminchannel[i] = 0
                self.tmaxchannel[i] = 0

            #..................define Tk object for data text........................
            # define self.root window
            self.bgkolor = 'lightgrey'
            self.root = Tk()
            self.root.configure(background=self.bgkolor, width = 2000)

            #set title
            self.root.title('Strip Chart')

            self.checks = {}
            for i in range(0,self.numchannel):
                self.checks[self.names[i]]='1'
               
            #define first frame for radio buttons
            self.row1 = Frame(self.root,height = 2, width = 4, background=self.bgkolor)
            self.row1.pack()

            for cname in self.names:
                self.checks[cname] = Variable()
                self.checks[cname].set('1')
                c = Checkbutton(self.row1, text=cname, variable=self.checks[cname],font=("Arial",9))
                c.pack(side ='left')

            #define second frame for zoom buttons
            self.row2 = Frame(self.root,height = 2, width = 4, background=self.bgkolor)
            self.row2.pack()

            #create zoom in button
            self.zoomb = Button(self.row2, text="->In<-", command=self.zoom, font=("Arial",9))
            #place zoom in button
            self.zoomb.pack(side = 'left', fill='both', expand=True, padx=4)
            #create zoom out button
            self.zoomb = Button(self.row2, text="<-Out->", command=self.zoomout, font=("Arial",9))
            #place zoom out button
            self.zoomb.pack(side = 'left',fill='both', expand=True, padx=4)
            #create zoom extents button
            self.extentsb = Button(self.row2, text="|<100%>|", command=self.extents, font=("Arial",9))
            #place zoom extents button
            self.extentsb.pack(side = 'left',fill='both', expand=True, padx=4)

            #define third frame for controls buttons
            self.row3 = Frame(self.root,height = 2, width = 4, background=self.bgkolor)
            self.row3.pack()

            #create and place rewind button
            self.screenshotb = Button(self.row3, text="Save Frame", command=self.screenshot, font=("Arial",9))
            self.screenshotb.pack(side = 'left')
            #create and place rewind button
            self.rewindb = Button(self.row3, text="|<", command=self.rewind, font=("Arial",9))
            self.rewindb.pack(side = 'left')
            #create and place fast backward button
            self.fbackb = Button(self.row3, text="<<", command=self.fback, font=("Arial",9))
            self.fbackb.pack(side = 'left')
            #create and place backward button
            self.backb = Button(self.row3, text="<-", command=self.back, font=("Arial",9))
            self.backb.pack(side = 'left')
            #create and place stop button
            self.stopb = Button(self.row3, text="STOP", command=self.stop, font=("Arial",9))
            self.stopb.pack(side = 'left')
            #create and place forward button
            self.forwardb = Button(self.row3, text="->", command=self.forward, font=("Arial",9))
            self.forwardb.pack(side = 'left')
            #create and place fast forward button
            self.fforwardb = Button(self.row3, text=">>", command=self.fforward, font=("Arial",9))
            self.fforwardb.pack(side = 'left')
            #create and place skip to end button
            self.skipendb = Button(self.row3, text=">|", command=self.skipend, font=("Arial",9))
            self.skipendb.pack(side = 'left')
            #create and place Jump to input box
            self.jumplabel = Label(self.row3, text = "Jump TOF: ", font=("Arial",9))
            self.jumplabel.pack(side = 'left')
            self.entry = Entry(self.row3, width = 10, font=("Arial",9))
            self.entry.pack(side = 'left')
            self.entry.bind('<Return>', self.jumptof)

            #define fourth frame for system messages
            self.row4 = Frame(self.root,height = 1, width = 60, background=self.bgkolor)
            self.row4.pack()
            self.mtext = Text(self.row4, width = 40, height = 1, background = self.bgkolor,font=("Arial",8))
            self.mtext.pack()


            #set text box size
            self.btext = Text(self.root, width = 30, height = self.numchannel*3+3, background = self.bgkolor,font=("Arial",8))
            #pack to show box
            self.btext.pack(side ='left',padx=10)


            # create self.canvas for chart
            self.chartcanvas = Canvas(self.root, width=600, height=400, background =self.bgkolor)
            self.chartcanvas.pack(side = 'left')
            
            #........................define figure for chart.....................   
            self.fig = plt.figure(facecolor = self.bgkolor)
            self.fig.set_size_inches(11, 8, forward=True)
            #set chart title
            self.fig.canvas.set_window_title('Telemetry')
            #add primary y axis to chart
            self.ax1 = self.fig.add_subplot(1,1,1, axisbg=self.bgkolor)

            self.canvas = FigureCanvasTkAgg(self.fig, self.chartcanvas)
            self.canvas.show()
            self.canvas.get_tk_widget().pack(side='left', fill=BOTH, expand=True)

            #counter for data lines recieved first line
            self.dcount = 0
            self.dmax = 0
            self.displaymin = 0 #lowest value displayed on x-axis of chart.
            self.displaymax = 0 #highest value displayed on x-axis of chart.
            self.mcount = 0

    #open  socket for tof and channel data
    def opensock(self,port):
        #..................Define and open socket..................
        self.TCP_IP = '127.0.0.1'
        self.TCP_PORT = port
        self.BUFFER_SIZE = 4*(self.numchannel+1)  # Change to match bytes in each data package
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.TCP_IP, self.TCP_PORT))
        self.s.listen(1)
        self.conn, self.addr = self.s.accept()
        
            
    #animation function....this is main looping function that fills window with data, chart with lines each animation frame
    def animate(self,i):
        #This section reads in data each frame.....stops reading when EOD is detected
        #get next "self.dinc" data points
        #test for end of data, EOD, flag
        if self.eodflag != '1':
            for i in range(0,self.dinc):
                self.data = self.conn.recv(self.BUFFER_SIZE)
                #no more data coming, shut down socket and set eodflag
                if not self.data:
                    self.eodflag = '1'
                    self.s.close()
                    self.dinc = 0
                    self.messagetext = '>>>>REALTIME DATA ENDED<<<<<\n'
                    print 'eod recieved'
                    break
                self.num = self.numchannel+1
                self.packet = struct.unpack('f'*self.num,self.data)
                self.tdata[self.dcount+i] = self.packet[0]
                self.tmax =  self.tdata[self.dcount+i]
                self.dmax = self.dcount+i
                for n in range(0,self.numchannel):
                    self.channeldata [n][self.dcount+i] = self.packet[n+1]
                    if self.channeldata[n][self.dcount+i] < self.minchannel[n]:
                        self.minchannel[n] = self.channeldata[n][self.dcount+i]
                        self.tminchannel[n] = self.tdata[self.dcount+i]                    
                    else:
                        if self.channeldata[n][self.dcount+i] > self.maxchannel[n]:
                            self.maxchannel[n] = self.channeldata[n][self.dcount+i]
                            self.tmaxchannel[n] = self.tdata[self.dcount+i]
                self.conn.send(str(self.tmax))  
        self.dcount = self.dcount + self.dinc

        
        #move self.displayinc frames.  Note self.displayinc can be negative
        self.displaymax = self.displaymax + self.displayinc
        
        #check display values are valid    
        if self.displaymax>self.dmax:
            self.displayinc = int(self.startdisplayinc*100/self.zuum)
            self.displaymax = self.dmax
        self.displaymin = self.displaymax - self.chartwidth
                
        if self.dcount > 1:
            if self.displaymin < 0:
                self.displaymin = 0
       
        if self.displaymax <= 0:
            self.displaymax = 0
            self.displayinc = self.startdisplayinc

        #Update text window
        #clear text window for next data set to be displayed
        self.btext.delete('1.0', END)    

        #show TOF
        self.wtext = "Realtime TOF: "+str(round(self.tmax,2))+' msec \n'
        self.btext.insert(INSERT, self.wtext)
       
        #value of end of x-axis  
        self.wtext = "Chart Max: "+str(round(self.tdata[self.displaymax],2))+' msec \n'
        self.btext.insert(INSERT, self.wtext)

        
        for i in range(0,self.numchannel):
            if self.checks[self.names[i]].get()=='1':
                self.wtext = self.names[i]+':\n'
                self.btext.insert(INSERT, self.wtext)
                self.tmaxstr =''
                self.tmaxstr = str(round(self.tmaxchannel[i],2))
                self.maxstr = ''
                maxstr = str(round(self.maxchannel[i],2))
                self.wtext = 'Max: '+ self.maxstr +' TOF: '+ self.tmaxstr+'\n'
                self.btext.insert(INSERT, self.wtext)
                self.tminstr = ''
                self.tminstr = str(round(self.tminchannel[i],2))
                minstr = ''
                minstr = str(round(self.minchannel[i],2))
                self.wtext = 'Min: '+ self.minstr +' TOF: '+ self.tminstr+'\n'
                self.btext.insert(INSERT, self.wtext)


        #Update message window
        #clear message window for next data set to be displayed
        self.mtext.delete('1.0', END)
        #this loop allow message to linger for reading with blocking other loops
        if self.mcount <10:
            self.mtext.insert(INSERT, self.messagetext)
            self.mcount = self.mcount+1
        else:
            self.mcount = 0
            self.messagetext =''

        #update box display        
        self.root.update()
         
        #Update chart
        self.ax1.clear()
        #ax2.clear()
        if self.displaymax >= self.chartwidth:
                tplot = self.tdata[self.displaymin:self.displaymax]
                for i in range(0, self.numchannel):
                    if self.checks[self.names[i]].get()=='1':
                        channel = self.channeldata[i][self.displaymin:self.displaymax]
                        self.ax1.plot(tplot,channel, label = self.names[i])
     
        else:
                #special case if data recieved is less than self.chartwidth
                tplot = self.tdata[0:self.displaymax]
                for i in range(0, self.numchannel):
                    if self.checks[self.names[i]].get()=='1':
                        channel = self.channeldata[i][0:self.displaymax]
                        self.ax1.plot(tplot,channel, label = self.names[i])
           
        #set up y axis legend                
        handles, labels = self.ax1.get_legend_handles_labels()
        #set legend location and font size
        self.ax1.legend(loc=3, shadow=True, fontsize='xx-small')

        #set chart title and fontsize
        plt.title('Realtime Data', fontsize = "small")
        #set axis label font sizes
        self.ax1.tick_params(labelsize='xx-small')
        #ax2.tick_params(labelsize='xx-small')

        self.ax1.yaxis.grid(color='black', linestyle='dashed')
        self.ax1.xaxis.grid(color='black', linestyle='dashed')

        #label each axis

        self.ax1.set_ylabel('IMU Data')
        self.ax1.set_xlabel('TOF msec')

         

    #create plot file of chart..............
    def screenshot(self):
            self.messagetext = "Saving Chart Frame..."
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
            shot = 'frame'+st+'.pdf'
            self.fig.savefig(shot)

    #rewind data function called by rewind button
    def rewind(self):
        self.messagetext = "Rewound first frame..."
        self.displayinc = 0
        self.displaymin = 0
        if self.dmax > self.chartwidth:
            self.displaymax = self.chartwidth
        else:
            self.displaymax = self.dmax
          
    #fast backward function
    def fback(self):
        self.messagetext = "Moving Backward Fast..."
        self.displayinc = int(-10*self.startdisplayinc*100/self.zuum)

    #backward function
    def back(self):
        self.messagetext = "Moving Backwards...."
        self.displayinc = int(-1*self.startdisplayinc*100/self.zuum)
       
    #stop function: freezes display of data and chart
    def stop(self):

        self.messagetext = "Strip Chart Stopped...."
        self.displayinc = 0
        
    #forward at normal increment 
    def forward(self):

        self.messagetext = "Moving Forward...."
        self.displayinc = int(self.startdisplayinc*100/self.zuum)
            
    #fast forward
    def fforward(self):

        self.messagetext = "Fast Forward...."
        self.displayinc = int(10*self.startdisplayinc*100/self.zuum)


    #skip to realtime data position
    def skipend(self):
        self.messagetext = "Skip Forward to Current Time..."
        self.displayinc = int(self.startdisplayinc*100/self.zuum)
        self.displaymax = self.dmax
        self.displaymin = self.displaymax - self.chartwidth
        if self.displaymin <= 1:
            self.displaymin = 1

    #zoom 2x
    def zoom(self):
        self.messagetext = "Zooming in +2X..."
        if self.chartwidth > 0.005 * self.initialchartwidth:
            self.chartwidth = self.chartwidth/2
            self.zuum = self.zuum * 2
            self.displayinc = int(self.displayinc/2)
            

    #zoom 1/2x
    def zoomout(self):
        self.messagetext = "Zooming out 1/2X...."
        self.chartwidth = self.chartwidth*2
        self.zuum  = int(self.zuum/2)

        
     
    #zoom extents
    def extents(self):
        self.messagetext = "Reset Zoom to 1X....."
        self.chartwidth = self.initialchartwidth
        self.displayinc = self.startdisplayinc
        self.zuum = 100

    #jump to TOF
    def jumptof(self,en):
       
        self.content = self.entry.get()
        self.dhold = 0
        try:
            self.midchart = float(self.content)
            self.entry.delete(0,END)
            for i in range(0, self.dmax):
                self.searchtdata = self.tdata[i]
                if self.searchtdata > self.midchart:
                    self.dhold = i
                    break
            self.displaymax = int(self.dhold + self.chartwidth/2)
            self.displayinc = 0
            self.messagetext = "Jumping to "+str(self.midchart)+" ....."
            
        except ValueError:
            print "Not a float"

        
#...............main program.............................
#create instance of StripChart            
chart1 = StripChart()
#set up channel names via text file
filename = 'ChannelNames.txt'
chart1.getnames(filename)
#open the port
port = 8889
chart1.opensock(port)
#start chart animation and data collection over socket
chart1.runanimation()
